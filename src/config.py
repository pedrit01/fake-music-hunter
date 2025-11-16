"""
Configuración y constantes del proyecto
"""

# Umbrales de frecuencia de corte esperados (en Hz)
CUTOFF_THRESHOLDS = {
    'mp3_320': 20000,   # MP3 320kbps debe tener contenido hasta ~20-21kHz
    'mp3_256': 19500,   # MP3 256kbps
    'mp3_192': 18000,   # MP3 192kbps
    'mp3_128': 16000,   # MP3 128kbps
    'flac': 20000,      # FLAC debe preservar todo el espectro
    'wav': 20000,       # WAV sin comprimir
    'flac_fake_threshold': 16500,  # Por debajo de esto es definitivamente fake
}

# Umbrales de clasificación
SUSPICIOUS_THRESHOLD = 2000  # Hz de margen para considerar "sospechoso"
FLAC_SUSPICIOUS_THRESHOLD = 3000  # Hz de margen más amplio para FLAC

# Extensiones de archivo soportadas
SUPPORTED_FORMATS = ['.mp3', '.flac', '.wav']

# Parámetros de análisis
ANALYSIS_DURATION = 30      # Segundos de audio a analizar (muestra)
SAMPLE_RATE = 44100         # Sample rate para análisis
FFT_SIZE = 4096             # Tamaño de la ventana FFT
HOP_LENGTH = 512            # Hop length para STFT

# Frecuencias de referencia
MIN_FREQUENCY = 16000       # Frecuencia mínima para análisis de corte
MAX_FREQUENCY = 22050       # Frecuencia máxima (Nyquist para 44.1kHz)

# Umbral de energía espectral (dB)
ENERGY_THRESHOLD = -60      # Threshold para considerar que hay contenido real

# Configuración de reportes
REPORT_FORMATS = ['console', 'csv', 'json']
DEFAULT_OUTPUT_DIR = 'output'

# Estados de clasificación
CLASS_LEGITIMATE = 'legitimate'
CLASS_FAKE = 'fake'
CLASS_SUSPICIOUS = 'suspicious'
CLASS_ERROR = 'error'

# Emojis para output CLI
EMOJI_MAP = {
    CLASS_LEGITIMATE: '✅',
    CLASS_FAKE: '❌',
    CLASS_SUSPICIOUS: '⚠️',
    CLASS_ERROR: '🚫'
}

# Colores para CLI (rich)
COLOR_MAP = {
    CLASS_LEGITIMATE: 'green',
    CLASS_FAKE: 'red',
    CLASS_SUSPICIOUS: 'yellow',
    CLASS_ERROR: 'dim red'
}
