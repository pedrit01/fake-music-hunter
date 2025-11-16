"""
Módulo para detectar archivos de audio falsos o upscaleados
"""

from typing import Dict, Tuple
from src.config import (
    CUTOFF_THRESHOLDS, SUSPICIOUS_THRESHOLD, FLAC_SUSPICIOUS_THRESHOLD,
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
        
        Usa un enfoque híbrido:
        1. Si tiene contenido por encima de 20 kHz → Lossless auténtico
        2. Si no, analiza la presencia espectral en 18-22 kHz
        
        Args:
            analysis_results: Resultados del análisis de AudioAnalyzer
            
        Returns:
            tuple: (clasificación, razón)
        """
        cutoff_freq = analysis_results.get('cutoff_frequency')
        spectral_presence = analysis_results.get('spectral_presence', 0)
        high_freq_energy = analysis_results.get('high_freq_energy', -100)
        has_content_above_20k = analysis_results.get('has_content_above_20k', False)
        
        if cutoff_freq is None and spectral_presence == 0:
            return CLASS_ERROR, "No se pudo calcular la frecuencia de corte"
        
        # ENFOQUE HÍBRIDO 1: Check rápido - si hay contenido >20 kHz es lossless
        if has_content_above_20k:
            return CLASS_LEGITIMATE, "Contenido detectado por encima de 20 kHz - FLAC lossless auténtico"
        
        # ENFOQUE HÍBRIDO 2: Usar presencia espectral como métrica principal
        # Si hay >30% de presencia en altas frecuencias (18-22 kHz), es lossless
        if spectral_presence > 30:
            return CLASS_LEGITIMATE, f"Presencia espectral {spectral_presence:.1f}% en altas frecuencias - FLAC lossless auténtico"
        
        # Si hay presencia moderada (15-30%), verificar energía
        elif spectral_presence > 15:
            if high_freq_energy > -60:
                return CLASS_LEGITIMATE, f"Presencia espectral {spectral_presence:.1f}% con energía adecuada - FLAC lossless"
            else:
                return CLASS_SUSPICIOUS, f"Presencia espectral {spectral_presence:.1f}% moderada - posible conversión de alta calidad"
        
        # Si hay poca presencia (5-15%), es sospechoso
        elif spectral_presence > 5:
            return CLASS_SUSPICIOUS, f"Presencia espectral baja ({spectral_presence:.1f}%) - posible conversión desde MP3 de calidad media"
        
        # Si hay muy poca o ninguna presencia (<5%), es fake
        else:
            if cutoff_freq and cutoff_freq < 16500:
                return CLASS_FAKE, "Sin contenido espectral en altas frecuencias - conversión desde MP3 de baja calidad"
            else:
                return CLASS_SUSPICIOUS, f"Presencia espectral muy baja ({spectral_presence:.1f}%) - posible producción con filtrado"
    
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
