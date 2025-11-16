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
    
    def calculate_cutoff_frequency(self) -> Optional[float]:
        """
        Calcula la frecuencia de corte del archivo de audio
        
        La frecuencia de corte es donde la energía espectral cae significativamente,
        indicando el límite real del contenido de audio.
        
        Returns:
            float: Frecuencia de corte en Hz, o None si hay error
        """
        if self.audio_data is None:
            if not self.load_audio():
                return None
        
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
            
            # Buscar frecuencia de corte desde las altas frecuencias hacia abajo
            # Buscamos donde la energía está por encima del threshold
            cutoff_freq = None
            
            for i in range(len(frequencies) - 1, -1, -1):
                if MIN_FREQUENCY <= frequencies[i] <= MAX_FREQUENCY:
                    if spectrum_db[i] > ENERGY_THRESHOLD:
                        cutoff_freq = frequencies[i]
                        break
            
            return cutoff_freq
            
        except Exception as e:
            print(f"Error calculando cutoff frequency para {self.file_path}: {e}")
            return None
    
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
        
        # Calcular características
        results['cutoff_frequency'] = self.calculate_cutoff_frequency()
        results['dynamic_range'] = self.calculate_dynamic_range()
        
        return results
