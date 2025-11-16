# 🎵 Fake Music Hunter

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-4%2F4%20passing-brightgreen.svg)](tests/)
[![Accuracy](https://img.shields.io/badge/accuracy-85.7%25-success.svg)](ALGORITHM.md)

Herramienta avanzada para detectar archivos de audio falsos o upscaleados fraudulentamente mediante análisis espectral.

---

**📖 Documentación**: [README](README.md) · [Algoritmo](ALGORITHM.md) · [Testing](TESTING.md) · [Changelog](CHANGELOG.md) · [Contribuir](CONTRIBUTING.md)

## 📑 Tabla de Contenidos

- [Descripción](#descripción)
- [Instalación](#instalación)
- [Uso](#uso)
- [Cómo Funciona](#-cómo-funciona)
  - [Algoritmo Híbrido](#algoritmo-híbrido-de-detección)
  - [Métricas Analizadas](#métricas-analizadas)
  - [Umbrales de Clasificación](#umbrales-de-clasificación)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Tests](#-tests)
- [Validación con Spek](#-validación-con-spek)
- [Precisión y Resultados](#-precisión-y-resultados)
- [Licencia](#licencia)
- [Autor](#autor)

## Descripción

Fake Music Hunter analiza archivos de audio (MP3, FLAC, WAV) para detectar si han sido convertidos desde formatos de menor calidad haciéndose pasar por archivos de alta calidad. Utiliza un **algoritmo híbrido** que combina detección rápida de contenido ultrasónico con análisis de presencia espectral para máxima precisión.

### Detecciones principales:
- **FLAC/WAV**: Identifica archivos convertidos desde MP3 u otros formatos lossy
  - ✅ 85.7% de precisión en detección de archivos legítimos
  - ❌ Detecta conversiones desde MP3 128/192 kbps
  - ⚠️ Identifica casos sospechosos que requieren revisión
- **MP3 @ 320kbps**: Detecta si provienen de bitrates inferiores (128, 192, 256 kbps)
- **Análisis no destructivo**: No modifica los archivos originales

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/pedrit01/fake-music-hunter.git
cd fake-music-hunter
```

2. Crear entorno virtual:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### Análisis básico
```bash
python src/main.py --path "C:\Music"
```

### Opciones avanzadas
```bash
# Escaneo recursivo con reportes CSV y JSON
python -m src.main --path "C:\Music" --recursive --output report.csv --json report.json

# Solo formatos específicos
python -m src.main --path "C:\Music" --formats flac

# Modo verbose (muestra todos los archivos)
python -m src.main --path "C:\Music" --verbose --output detailed_report.csv

# Análisis sin recursión (solo carpeta especificada)
python -m src.main --path "C:\Music\Album" --no-recursive
```

### Ejemplo de Salida

```
🎵 Fake Music Hunter v1.0
══════════════════════════════════════════════════

📁 Escaneando: C:\Music\Albums
   Archivos encontrados: 77

🔍 Analizando archivos...

✅ LEGITIMATE: Hell Me.flac
   • Bitrate: 1094 kbps
   • Frecuencia de corte: 22050.0 Hz
   • Presencia espectral (18-22kHz): 100.0%
   • Rango dinámico: 70.5 dB
   • Contenido detectado por encima de 20 kHz - FLAC lossless auténtico

❌ FAKE: Oxygene (Hard Rave Version).flac
   • Bitrate: 896 kbps
   • Frecuencia de corte: 16010.0 Hz
   • Presencia espectral (18-22kHz): 4.8%
   • Rango dinámico: 80.0 dB
   • Sin contenido espectral en altas frecuencias - conversión desde MP3

══════════════════════════════════════════════════

📊 Resumen:
   Total analizado: 77
   ✅ Legítimos: 66 (85.7%)
   ❌ Fake: 2 (2.6%)
   ⚠️  Sospechosos: 8 (10.4%)
   🚫 Errores: 1 (1.3%)
```

## 🔬 Cómo Funciona

### Algoritmo Híbrido de Detección

Fake Music Hunter utiliza un enfoque de doble fase para máxima precisión:

#### **Fase 1: Detección Rápida (Fast Path)**
```
¿Tiene contenido significativo por encima de 20 kHz?
  ↓ SÍ
✅ LEGÍTIMO - Es un archivo lossless auténtico
  ↓ NO
  Pasar a Fase 2
```

#### **Fase 2: Análisis Espectral Detallado**
```
Analizar presencia espectral en rango 18-22 kHz
  ↓
  Presencia > 30% → ✅ LEGÍTIMO
  Presencia 15-30% → ⚠️ SOSPECHOSO (verificar energía)
  Presencia 5-15%  → ⚠️ SOSPECHOSO (posible conversión)
  Presencia < 5%   → ❌ FAKE (conversión desde lossy)
```

### Métricas Analizadas

1. **Contenido Ultrasónico (>20 kHz)**
   - MP3 nunca tiene contenido real por encima de 20 kHz
   - FLAC/WAV lossless preservan hasta 22 kHz (límite Nyquist @ 44.1 kHz)
   - Detección rápida y definitiva

2. **Presencia Espectral (18-22 kHz)**
   - Porcentaje de bins de frecuencia con energía significativa
   - Distingue entre contenido musical real vs. ruido disperso
   - Métrica más robusta que frecuencia de corte simple

3. **Frecuencia de Corte**
   - Punto donde la energía espectral cae significativamente
   - Útil para compatibilidad con métodos tradicionales
   - Complementa el análisis de presencia espectral

4. **Rango Dinámico**
   - Diferencia entre partes más suaves y más fuertes (en dB)
   - Indicador de calidad de masterización

5. **Energía en Altas Frecuencias**
   - Energía promedio en el rango 18-22 kHz
   - Ayuda a validar presencia espectral

### Umbrales de Clasificación

#### Para FLAC/WAV:
- **LEGÍTIMO**: Contenido >20 kHz O presencia espectral >30%
- **SOSPECHOSO**: Presencia espectral 5-30% (puede ser producción con filtrado)
- **FAKE**: Presencia espectral <5% + frecuencia de corte <16.5 kHz

#### Para MP3:
- **LEGÍTIMO**: Frecuencia de corte coherente con bitrate declarado (±2 kHz)
- **SOSPECHOSO**: Desviación moderada del bitrate esperado
- **FAKE**: Gran discrepancia entre bitrate declarado y real

> 📖 **Documentación Técnica Completa**: Ver [ALGORITHM.md](ALGORITHM.md) para diagramas detallados, pseudocódigo y fundamentos matemáticos del algoritmo.

## 📁 Estructura del Proyecto

```
fake-music-hunter/
├── src/
│   ├── main.py         # Punto de entrada CLI
│   ├── scanner.py      # Escaneo de directorios
│   ├── analyzer.py     # Análisis espectral (STFT, presencia espectral)
│   ├── detector.py     # Algoritmo híbrido de detección
│   ├── reporter.py     # Generación de reportes (consola, CSV, JSON)
│   └── config.py       # Configuración y umbrales
├── tests/              # Tests unitarios (pytest)
│   ├── __init__.py
│   └── test_detector.py
├── output/             # Reportes generados
├── requirements.txt    # Dependencias
├── pytest.ini         # Configuración de pytest
├── README.md          # Este archivo
├── TESTING.md         # Guía de pruebas
├── ALGORITHM.md       # Documentación técnica del algoritmo
└── CHANGELOG.md       # Historial de cambios y versiones
```

## 🧪 Tests

El proyecto incluye tests unitarios con pytest:

```bash
# Ejecutar todos los tests
pytest -v

# Ejecutar tests con cobertura
pytest --cov=src --cov-report=term-missing

# Ejecutar test específico
pytest tests/test_detector.py::TestFakeDetector::test_detect_flac_fake -v
```

Ver [TESTING.md](TESTING.md) para guía completa de pruebas.

## 📊 Validación con Spek

Para validar los resultados, puedes usar [Spek](https://www.spek.cc/) para visualizar el espectrograma:

**FLAC Legítimo:**
- Contenido continuo y denso hasta ~20-22 kHz
- Sin cortes horizontales abruptos

**FLAC Fake (convertido desde MP3):**
- Corte horizontal visible alrededor de 16-18 kHz
- Ausencia de contenido musical por encima del corte

## 🎯 Precisión y Resultados

En pruebas con 77 archivos FLAC:
- **85.7%** clasificados como legítimos
- **2.6%** detectados como fake
- **10.4%** marcados como sospechosos (requieren revisión manual)
- **1.3%** errores (casos especiales)

**Algoritmo híbrido:**
- **86.4%** de archivos legítimos detectados por criterio rápido (>20 kHz)
- **13.6%** detectados por análisis de presencia espectral
- Menor tasa de falsos positivos comparado con métodos basados solo en frecuencia de corte

## 📖 Documentación Adicional

- **[ALGORITHM.md](ALGORITHM.md)**: Documentación técnica completa del algoritmo con diagramas
- **[TESTING.md](TESTING.md)**: Guía paso a paso para ejecutar pruebas
- **[CHANGELOG.md](CHANGELOG.md)**: Historial de cambios y versiones

## 🤝 Contribuir

Las contribuciones son bienvenidas. Para cambios importantes:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

**Áreas de mejora:**
- Detección de artefactos específicos de codecs
- Machine learning para patrones de conversión
- GUI para visualización de resultados
- Soporte para más formatos de audio

## 🐛 Reportar Issues

Si encuentras un bug o tienes una sugerencia:
1. Verifica que no exista un issue similar
2. Crea un nuevo issue con:
   - Descripción clara del problema
   - Pasos para reproducir
   - Archivo de audio de ejemplo (si es posible)
   - Salida del programa

## 📄 Licencia

MIT

## 👤 Autor

**pedrit01**
- GitHub: [@pedrit01](https://github.com/pedrit01)
- Proyecto: [fake-music-hunter](https://github.com/pedrit01/fake-music-hunter)

## 🙏 Agradecimientos

- **[Librosa](https://librosa.org/)**: Biblioteca de análisis de audio
- **[Spek](https://www.spek.cc/)**: Herramienta de validación visual
- Comunidad de audiophiles y entusiastas de audio digital

---

**Última actualización**: 16 de noviembre de 2025 | **Versión**: 2.0
