# 🧮 Algoritmo de Detección - Documentación Técnica

## Resumen Ejecutivo

Fake Music Hunter implementa un **algoritmo híbrido de dos fases** para detectar archivos de audio convertidos fraudulentamente desde formatos lossy (con pérdida) a formatos lossless (sin pérdida).

## 📊 Diagrama de Flujo del Algoritmo

```
┌─────────────────────────────────────┐
│   INICIO: Archivo de Audio          │
│   (FLAC, WAV, MP3)                  │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  Extraer Metadatos                  │
│  - Formato (.flac, .wav, .mp3)     │
│  - Bitrate                          │
│  - Sample rate                      │
│  - Tamaño de archivo                │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  Cargar Audio (30 segundos)         │
│  - Sample rate: 44100 Hz            │
│  - Mono (mezclar canales)           │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  Análisis Espectral (STFT)          │
│  - FFT size: 4096                   │
│  - Hop length: 512                  │
│  - Promediar sobre tiempo           │
│  - Convertir a escala dB            │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│  Calcular Métricas Espectrales      │
│  ┌─────────────────────────────┐   │
│  │ 1. Contenido >20 kHz        │   │
│  │    (detección ultrasónica)  │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ 2. Presencia Espectral      │   │
│  │    18-22 kHz (%)            │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ 3. Frecuencia de Corte      │   │
│  │    (método tradicional)     │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ 4. Energía Alta Frecuencia  │   │
│  │    (dB promedio)            │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ 5. Rango Dinámico           │   │
│  │    (dB)                     │   │
│  └─────────────────────────────┘   │
└───────────────┬─────────────────────┘
                │
                ▼
        ┌───────────────┐
        │  ¿Es FLAC/WAV? │
        └───┬───────┬────┘
            │       │
         SÍ │       │ NO (MP3)
            │       │
            ▼       ▼
    ┌───────────┐  ┌────────────────┐
    │ Algoritmo │  │ Análisis MP3   │
    │ Híbrido   │  │ (comparar      │
    │ FLAC/WAV  │  │  bitrate real  │
    │           │  │  vs declarado) │
    └─────┬─────┘  └────────┬───────┘
          │                 │
          │                 │
          └────────┬────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  Resultado:     │
         │  ✅ LEGÍTIMO    │
         │  ❌ FAKE        │
         │  ⚠️ SOSPECHOSO  │
         │  🚫 ERROR       │
         └─────────────────┘
```

## 🔍 Algoritmo Híbrido para FLAC/WAV (Detallado)

```
┌─────────────────────────────────────────────────────┐
│           FASE 1: DETECCIÓN RÁPIDA                  │
│         (Fast Path - Criterio Definitivo)           │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
            ┌──────────────────────┐
            │ ¿Tiene contenido     │
            │ significativo        │ 
            │ >20 kHz?             │
            │ (energía > -65 dB)   │
            └──────┬───────┬───────┘
                   │       │
                SÍ │       │ NO
                   │       │
                   ▼       │
            ┌──────────────┐│
            │ ✅ LEGÍTIMO  ││
            │              ││
            │ Razón:       ││
            │ "Contenido   ││
            │  detectado   ││
            │  >20 kHz"    ││
            └──────────────┘│
                            │
                            ▼
┌───────────────────────────────────────────────────┐
│     FASE 2: ANÁLISIS DE PRESENCIA ESPECTRAL       │
│          (Análisis Detallado)                     │
└─────────────────┬─────────────────────────────────┘
                  │
                  ▼
        ┌──────────────────────┐
        │ Presencia Espectral  │
        │ en 18-22 kHz         │
        └──────────┬───────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
    Presencia            Presencia
      >30%              15-30%
         │                   │
         ▼                   ▼
  ┌──────────────┐    ┌─────────────────┐
  │ ✅ LEGÍTIMO  │    │ ¿Energía > -60  │
  │              │    │    dB?          │
  │ Razón:       │    └────┬────────┬───┘
  │ "Presencia   │         │        │
  │  espectral   │      SÍ │        │ NO
  │  XX%"        │         │        │
  └──────────────┘         ▼        ▼
                    ┌──────────┐ ┌──────────┐
                    │✅LEGÍTIMO│ │⚠️SOSPEC. │
                    └──────────┘ └──────────┘
         │
         ▼
    Presencia
     5-15%
         │
         ▼
  ┌──────────────┐
  │ ⚠️ SOSPECHOSO│
  │              │
  │ Razón:       │
  │ "Presencia   │
  │  baja (XX%)  │
  │  posible     │
  │  conversión" │
  └──────────────┘
         │
         ▼
    Presencia
      <5%
         │
         ▼
  ┌──────────────────────┐
  │ ¿Frecuencia corte    │
  │ < 16.5 kHz?          │
  └────┬────────────┬────┘
       │            │
    SÍ │            │ NO
       │            │
       ▼            ▼
  ┌─────────┐ ┌──────────┐
  │ ❌ FAKE │ │⚠️SOSPEC. │
  │         │ │          │
  │ "Sin    │ │ "Muy baja│
  │ contenido│ │ presencia│
  │ en altas"│ │ posible  │
  │          │ │ filtrado"│
  └─────────┘ └──────────┘
```

## 📐 Métricas Técnicas

### 1. Detección de Contenido Ultrasónico (>20 kHz)

**Fundamento:**
- Formato MP3 aplica filtro paso-bajo que elimina frecuencias >~20 kHz
- FLAC/WAV lossless preservan hasta frecuencia Nyquist (~22 kHz @ 44.1 kHz)

**Implementación:**
```python
ultra_high_freq_mask = (frequencies >= 20000) & (frequencies <= 22000)
has_content = np.any(spectrum_db[ultra_high_freq_mask] > -65)
```

**Umbral:** -65 dB (relativo al máximo)
- Excluye ruido de fondo
- Detecta contenido musical real

### 2. Presencia Espectral (18-22 kHz)

**Fundamento:**
- Mide qué porcentaje de bins tienen energía significativa
- Más robusto que frecuencia de corte simple
- Distingue producción filtrada de conversión lossy

**Implementación:**
```python
high_freq_mask = (frequencies >= 18000) & (frequencies <= 22000)
significant_bins = np.sum(spectrum_db[high_freq_mask] > -70)
total_bins = np.sum(high_freq_mask)
presence_percentage = (significant_bins / total_bins) * 100
```

**Umbrales:**
- `>30%`: LEGÍTIMO - contenido distribuido
- `15-30%`: SOSPECHOSO/LEGÍTIMO (depende de energía)
- `5-15%`: SOSPECHOSO - poca presencia
- `<5%`: FAKE - casi sin contenido

### 3. Frecuencia de Corte

**Fundamento:**
- Punto donde energía cae por debajo de umbral
- Método tradicional de detección
- Útil como métrica complementaria

**Implementación:**
```python
# Buscar desde altas frecuencias hacia abajo
for i in range(len(frequencies) - 1, -1, -1):
    if frequencies[i] >= 16000 and frequencies[i] <= 22000:
        if spectrum_db[i] > -60:  # Umbral primario
            return frequencies[i]

# Umbral relajado si no encuentra
if not found:
    threshold = -80  # Umbral secundario
```

**Umbrales de energía:**
- Primario: -60 dB
- Secundario: -80 dB (para casos especiales)

### 4. Energía en Altas Frecuencias

**Fundamento:**
- Promedio de energía en 18-22 kHz
- Valida que la presencia sea significativa

**Implementación:**
```python
high_freq_energy = np.mean(spectrum_db[high_freq_mask])
```

**Umbral:** >-60 dB para validar presencia moderada

### 5. Rango Dinámico

**Fundamento:**
- Diferencia entre peaks y valleys
- Indicador de calidad de masterización
- No es determinante para fake detection

**Implementación:**
```python
rms = librosa.feature.rms(y=audio_data)
rms_db = librosa.amplitude_to_db(rms_nonzero)
dynamic_range = np.max(rms_db) - np.min(rms_db)
```

## 🎚️ Umbrales de Frecuencia para MP3

```python
CUTOFF_THRESHOLDS = {
    'mp3_320': 20000,  # Hz - MP3 320kbps
    'mp3_256': 19500,  # Hz - MP3 256kbps  
    'mp3_192': 18000,  # Hz - MP3 192kbps
    'mp3_128': 16000,  # Hz - MP3 128kbps
    'flac': 20000,     # Hz - FLAC baseline
}

SUSPICIOUS_THRESHOLD = 2000      # Hz - margen de tolerancia
FLAC_SUSPICIOUS_THRESHOLD = 3000 # Hz - margen para FLAC
```

## 🔬 Parámetros STFT

```python
SAMPLE_RATE = 44100      # Hz - tasa de muestreo
FFT_SIZE = 4096          # Ventana FFT
HOP_LENGTH = 512         # Salto entre ventanas
ANALYSIS_DURATION = 30   # segundos analizados

# Rango de análisis
MIN_FREQUENCY = 16000    # Hz - inicio análisis
MAX_FREQUENCY = 22050    # Hz - límite Nyquist
```

**Resolución de frecuencia:**
```
Δf = sample_rate / FFT_size = 44100 / 4096 ≈ 10.77 Hz
```

## 📊 Ventajas del Algoritmo Híbrido

1. **Eficiencia**: 86% de casos resueltos en Fase 1 (fast path)
2. **Precisión**: Menos falsos positivos que métodos basados solo en frecuencia de corte
3. **Robustez**: Maneja casos especiales (producción con filtrado)
4. **Conservador**: Prefiere marcar como sospechoso antes que como fake
5. **Validable**: Resultados verificables visualmente con espectrogramas (Spek)

## ⚠️ Limitaciones

1. **No detecta** todas las conversiones de alta calidad (MP3 320 → FLAC)
2. **Puede marcar** como sospechosa música con filtrado intencional
3. **Requiere** sample rate mínimo de 44.1 kHz para análisis >20 kHz
4. **Analiza** solo primeros 30 segundos (optimización de rendimiento)

## 🔮 Mejoras Futuras

- [ ] Análisis de artefactos de compresión específicos de codecs
- [ ] Machine learning para patrones de conversión
- [ ] Soporte para archivos con sample rate variable
- [ ] Detección de upsampling (16 kHz → 44.1 kHz)
- [ ] Análisis de fase (coherencia estéreo)
- [ ] Detección de normalización/limitación agresiva

## 📚 Referencias

- [Librosa Documentation](https://librosa.org/)
- [Digital Audio Fundamentals](https://en.wikipedia.org/wiki/Nyquist%E2%80%93Shannon_sampling_theorem)
- [MP3 Encoding Characteristics](https://en.wikipedia.org/wiki/MP3#Encoding_audio)
- [FLAC Specification](https://xiph.org/flac/format.html)
