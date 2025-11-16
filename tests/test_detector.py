"""
Tests para el módulo detector
"""
import pytest
from src.detector import FakeDetector


class TestFakeDetector:
    """Tests para la clase FakeDetector"""
    
    def test_detector_methods_exist(self):
        """Test de existencia de métodos del detector"""
        assert hasattr(FakeDetector, 'detect')
        assert hasattr(FakeDetector, 'detect_mp3')
        assert hasattr(FakeDetector, 'detect_flac')
        assert hasattr(FakeDetector, 'detect_wav')
    
    def test_detect_mp3_fake(self):
        """Test de detección de MP3 fake"""
        analysis = {
            'format': '.mp3',
            'bitrate': 320000,
            'cutoff_frequency': 16000  # Muy bajo para 320 kbps
        }
        classification, _ = FakeDetector.detect_mp3(analysis)
        assert classification == 'fake'
    
    def test_detect_flac_fake(self):
        """Test de detección de FLAC fake"""
        analysis = {
            'format': '.flac',
            'cutoff_frequency': 16000  # Indica conversión desde MP3
        }
        classification, _ = FakeDetector.detect_flac(analysis)
        assert classification == 'fake'
    
    def test_detect_error_no_cutoff(self):
        """Test de manejo de error cuando no hay frecuencia de corte"""
        analysis = {
            'format': '.mp3',
            'bitrate': 320000
        }
        classification, _ = FakeDetector.detect_mp3(analysis)
        assert classification == 'error'
