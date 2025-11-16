"""
Módulo para detectar archivos de audio falsos o upscaleados
"""

from typing import Dict, Tuple
from src.config import (
    CUTOFF_THRESHOLDS, SUSPICIOUS_THRESHOLD,
    CLASS_LEGITIMATE, CLASS_FAKE, CLASS_SUSPICIOUS, CLASS_ERROR
)


class FakeDetector:
    """Detecta si un archivo de audio es falso basándose en el análisis espectral"""
    
    @staticmethod
    def detect_mp3(analysis_results: Dict) -> Tuple[str, str]:
        """
        Detecta si un archivo MP3 es falso
        
        Args:
            analysis_results: Resultados del análisis de AudioAnalyzer
            
        Returns:
            tuple: (clasificación, razón)
        """
        cutoff_freq = analysis_results.get('cutoff_frequency')
        bitrate = analysis_results.get('bitrate', 0)
        
        if cutoff_freq is None:
            return CLASS_ERROR, "No se pudo calcular la frecuencia de corte"
        
        # Convertir bitrate a kbps
        bitrate_kbps = bitrate / 1000 if bitrate else 0
        
        # Determinar umbral esperado según bitrate declarado
        if bitrate_kbps >= 320:
            expected_cutoff = CUTOFF_THRESHOLDS['mp3_320']
            origin = "MP3 320 kbps"
        elif bitrate_kbps >= 256:
            expected_cutoff = CUTOFF_THRESHOLDS['mp3_256']
            origin = "MP3 256 kbps"
        elif bitrate_kbps >= 192:
            expected_cutoff = CUTOFF_THRESHOLDS['mp3_192']
            origin = "MP3 192 kbps"
        else:
            expected_cutoff = CUTOFF_THRESHOLDS['mp3_128']
            origin = "MP3 128 kbps"
        
        # Detectar patrón de fake
        if cutoff_freq < CUTOFF_THRESHOLDS['mp3_128'] - SUSPICIOUS_THRESHOLD:
            return CLASS_FAKE, f"Frecuencia de corte muy baja ({cutoff_freq:.0f} Hz), probable archivo corrupto o de muy baja calidad"
        
        elif bitrate_kbps >= 320:
            # MP3 @ 320 kbps
            if cutoff_freq < CUTOFF_THRESHOLDS['mp3_192']:
                # Definitivamente fake - probablemente de 128 kbps
                return CLASS_FAKE, f"Declarado como 320 kbps pero frecuencia de corte de {cutoff_freq:.0f} Hz indica origen 128 kbps"
            
            elif cutoff_freq < CUTOFF_THRESHOLDS['mp3_256'] - SUSPICIOUS_THRESHOLD:
                # Sospechoso - probablemente de 192 kbps
                return CLASS_FAKE, f"Declarado como 320 kbps pero frecuencia de corte de {cutoff_freq:.0f} Hz indica origen 192 kbps"
            
            elif cutoff_freq < CUTOFF_THRESHOLDS['mp3_320'] - SUSPICIOUS_THRESHOLD:
                # Sospechoso - podría ser 256 kbps
                return CLASS_SUSPICIOUS, f"Declarado como 320 kbps pero frecuencia de corte de {cutoff_freq:.0f} Hz indica posible origen 256 kbps"
            
            else:
                return CLASS_LEGITIMATE, f"Frecuencia de corte {cutoff_freq:.0f} Hz coherente con MP3 320 kbps"
        
        else:
            # Para bitrates menores, simplemente verificar coherencia
            if cutoff_freq >= expected_cutoff - SUSPICIOUS_THRESHOLD:
                return CLASS_LEGITIMATE, f"Frecuencia de corte {cutoff_freq:.0f} Hz coherente con bitrate declarado ({bitrate_kbps:.0f} kbps)"
            else:
                return CLASS_SUSPICIOUS, f"Frecuencia de corte {cutoff_freq:.0f} Hz menor a la esperada para {bitrate_kbps:.0f} kbps"
    
    @staticmethod
    def detect_flac(analysis_results: Dict) -> Tuple[str, str]:
        """
        Detecta si un archivo FLAC es falso (convertido desde lossy)
        
        Args:
            analysis_results: Resultados del análisis de AudioAnalyzer
            
        Returns:
            tuple: (clasificación, razón)
        """
        cutoff_freq = analysis_results.get('cutoff_frequency')
        
        if cutoff_freq is None:
            return CLASS_ERROR, "No se pudo calcular la frecuencia de corte"
        
        expected_cutoff = CUTOFF_THRESHOLDS['flac']
        
        # FLAC debería preservar todo el espectro audible
        if cutoff_freq < CUTOFF_THRESHOLDS['mp3_128']:
            return CLASS_FAKE, f"Frecuencia de corte de {cutoff_freq:.0f} Hz indica conversión desde MP3 128 kbps o inferior"
        
        elif cutoff_freq < CUTOFF_THRESHOLDS['mp3_192']:
            return CLASS_FAKE, f"Frecuencia de corte de {cutoff_freq:.0f} Hz indica probable conversión desde MP3 128-192 kbps"
        
        elif cutoff_freq < CUTOFF_THRESHOLDS['mp3_256']:
            return CLASS_SUSPICIOUS, f"Frecuencia de corte de {cutoff_freq:.0f} Hz indica posible conversión desde MP3 192-256 kbps"
        
        elif cutoff_freq < expected_cutoff - SUSPICIOUS_THRESHOLD:
            return CLASS_SUSPICIOUS, f"Frecuencia de corte de {cutoff_freq:.0f} Hz es sospechosamente baja para FLAC"
        
        else:
            return CLASS_LEGITIMATE, f"Frecuencia de corte {cutoff_freq:.0f} Hz coherente con FLAC lossless"
    
    @staticmethod
    def detect_wav(analysis_results: Dict) -> Tuple[str, str]:
        """
        Detecta si un archivo WAV es falso (convertido desde lossy)
        
        Args:
            analysis_results: Resultados del análisis de AudioAnalyzer
            
        Returns:
            tuple: (clasificación, razón)
        """
        # WAV sin comprimir debería tener el espectro completo, similar a FLAC
        return FakeDetector.detect_flac(analysis_results)
    
    @staticmethod
    def detect(analysis_results: Dict) -> Tuple[str, str]:
        """
        Detecta si un archivo es falso basándose en su formato
        
        Args:
            analysis_results: Resultados del análisis de AudioAnalyzer
            
        Returns:
            tuple: (clasificación, razón)
        """
        file_format = analysis_results.get('format', '').lower()
        
        if 'error' in analysis_results:
            return CLASS_ERROR, analysis_results['error']
        
        if file_format == '.mp3':
            return FakeDetector.detect_mp3(analysis_results)
        
        elif file_format == '.flac':
            return FakeDetector.detect_flac(analysis_results)
        
        elif file_format == '.wav':
            return FakeDetector.detect_wav(analysis_results)
        
        else:
            return CLASS_ERROR, f"Formato no soportado: {file_format}"
