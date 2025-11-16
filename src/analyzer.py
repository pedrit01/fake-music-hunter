"""
Módulo para análisis espectral de archivos de audio
"""

import librosa
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
from mutagen import File as MutagenFile
from src.config import (
    ANALYSIS_DURATION, SAMPLE_RATE, FFT_SIZE, 
    HOP_LENGTH, MIN_FREQUENCY, MAX_FREQUENCY, ENERGY_THRESHOLD
)


class AudioAnalyzer:
    """Analiza archivos de audio para extraer características espectrales"""
    
    def __init__(self, file_path: Path):
        """
        Inicializa el analizador
        
        Args:
            file_path: Ruta al archivo de audio
        """
        self.file_path = file_path
        self.metadata = None
        self.audio_data = None
        self.sr = None
        
    def load_audio(self) -> bool:
        """
        Carga el archivo de audio
        
        Returns:
            bool: True si se cargó correctamente, False en caso contrario
        """
        try:
            # Cargar solo los primeros ANALYSIS_DURATION segundos
            self.audio_data, self.sr = librosa.load(
                str(self.file_path),
                sr=SAMPLE_RATE,
                duration=ANALYSIS_DURATION,
                mono=True
            )
            return True
        except Exception as e:
            print(f"Error cargando {self.file_path}: {e}")
            return False
    
    def extract_metadata(self) -> Dict:
        """
        Extrae metadatos del archivo (bitrate, sample rate, etc.)
        
        Returns:
            dict: Diccionario con metadatos
        """
        try:
            audio_file = MutagenFile(str(self.file_path))
            
            metadata = {
                'format': self.file_path.suffix.lower(),
                'bitrate': getattr(audio_file.info, 'bitrate', None),
                'sample_rate': getattr(audio_file.info, 'sample_rate', None),
                'channels': getattr(audio_file.info, 'channels', None),
                'length': getattr(audio_file.info, 'length', None),
                'file_size': self.file_path.stat().st_size,
            }
            
            self.metadata = metadata
            return metadata
            
        except Exception as e:
            print(f"Error extrayendo metadatos de {self.file_path}: {e}")
            return {}
    
    def calculate_spectral_stats(self) -> Dict[str, Optional[float]]:
        """
        Calcula estadísticas espectrales del archivo de audio
        
        Analiza la distribución de energía en diferentes rangos de frecuencia
        para determinar si el archivo es lossless o convertido desde lossy.
        
        Returns:
            dict: Diccionario con estadísticas espectrales
        """
        if self.audio_data is None:
            if not self.load_audio():
                return {
                    'cutoff_frequency': None,
                    'high_freq_energy': None,
                    'spectral_presence': None
                }
        
        try:
            # Calcular STFT (Short-Time Fourier Transform)
            stft = librosa.stft(
                self.audio_data,
                n_fft=FFT_SIZE,
                hop_length=HOP_LENGTH
            )
            
            # Obtener magnitud del espectro
            magnitude = np.abs(stft)
            
            # Promediar sobre el tiempo
            avg_spectrum = np.mean(magnitude, axis=1)
            
            # Convertir a dB
            spectrum_db = librosa.amplitude_to_db(avg_spectrum, ref=np.max)
            
            # Obtener frecuencias correspondientes
            frequencies = librosa.fft_frequencies(sr=self.sr, n_fft=FFT_SIZE)
            
            # Calcular energía promedio en el rango de altas frecuencias (18-22 kHz)
            high_freq_mask = (frequencies >= 18000) & (frequencies <= 22000)
            high_freq_energy = np.mean(spectrum_db[high_freq_mask]) if np.any(high_freq_mask) else -100
            
            # Contar cuántos bins tienen energía significativa en altas frecuencias
            # (por encima de -70 dB relativo)
            significant_high_freq = np.sum(spectrum_db[high_freq_mask] > -70)
            total_high_freq_bins = np.sum(high_freq_mask)
            spectral_presence = (significant_high_freq / total_high_freq_bins * 100) if total_high_freq_bins > 0 else 0
            
            # Detección simple: ¿hay contenido significativo por encima de 20 kHz?
            ultra_high_freq_mask = (frequencies >= 20000) & (frequencies <= 22000)
            has_content_above_20k = np.any(spectrum_db[ultra_high_freq_mask] > -65) if np.any(ultra_high_freq_mask) else False
            
            # Buscar frecuencia de corte tradicional (para compatibilidad)
            cutoff_freq = None
            for i in range(len(frequencies) - 1, -1, -1):
                if MIN_FREQUENCY <= frequencies[i] <= MAX_FREQUENCY:
                    if spectrum_db[i] > ENERGY_THRESHOLD:
                        cutoff_freq = frequencies[i]
                        break
            
            # Si no encontramos con umbral estricto, intentar con uno más permisivo
            if cutoff_freq is None:
                relaxed_threshold = ENERGY_THRESHOLD - 20
                for i in range(len(frequencies) - 1, -1, -1):
                    if MIN_FREQUENCY <= frequencies[i] <= MAX_FREQUENCY:
                        if spectrum_db[i] > relaxed_threshold:
                            cutoff_freq = frequencies[i]
                            break
            
            return {
                'cutoff_frequency': cutoff_freq,
                'high_freq_energy': float(high_freq_energy),
                'spectral_presence': float(spectral_presence),
                'has_content_above_20k': bool(has_content_above_20k)
            }
            
        except Exception as e:
            print(f"Error calculando estadísticas espectrales para {self.file_path}: {e}")
            return {
                'cutoff_frequency': None,
                'high_freq_energy': None,
                'spectral_presence': None,
                'has_content_above_20k': False
            }
    
    def calculate_dynamic_range(self) -> Optional[float]:
        """
        Calcula el rango dinámico del audio en dB
        
        Returns:
            float: Rango dinámico en dB, o None si hay error
        """
        if self.audio_data is None:
            if not self.load_audio():
                return None
        
        try:
            # Calcular RMS por frames
            rms = librosa.feature.rms(y=self.audio_data, hop_length=HOP_LENGTH)[0]
            
            # Filtrar silencio
            rms_nonzero = rms[rms > 0]
            
            if len(rms_nonzero) == 0:
                return None
            
            # Convertir a dB
            rms_db = librosa.amplitude_to_db(rms_nonzero)
            
            # Calcular rango dinámico
            dynamic_range = np.max(rms_db) - np.min(rms_db)
            
            return float(dynamic_range)
            
        except Exception as e:
            print(f"Error calculando dynamic range para {self.file_path}: {e}")
            return None
    
    def analyze(self) -> Dict:
        """
        Realiza un análisis completo del archivo
        
        Returns:
            dict: Diccionario con todos los resultados del análisis
        """
        results = {
            'file_path': str(self.file_path),
            'file_name': self.file_path.name,
        }
        
        # Extraer metadatos
        metadata = self.extract_metadata()
        results.update(metadata)
        
        # Cargar audio
        if not self.load_audio():
            results['error'] = 'No se pudo cargar el archivo de audio'
            return results
        
        # Calcular estadísticas espectrales (incluye cutoff_frequency)
        spectral_stats = self.calculate_spectral_stats()
        results.update(spectral_stats)
        
        # Calcular rango dinámico
        results['dynamic_range'] = self.calculate_dynamic_range()
        
        return results
