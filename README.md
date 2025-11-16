# 🎵 Fake Music Hunter

Herramienta para detectar archivos de audio falsos o upscaleados fraudulentamente.

## Descripción

Fake Music Hunter analiza archivos de audio (MP3, FLAC, WAV) para detectar si han sido convertidos desde formatos de menor calidad haciéndose pasar por archivos de alta calidad.

### Detecciones principales:
- **MP3 @ 320kbps**: Detecta si provienen de bitrates inferiores (128, 192 kbps)
- **FLAC**: Identifica archivos convertidos desde formatos lossy
- **WAV**: Verifica la calidad real del audio sin comprimir

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
# Escaneo recursivo con reporte detallado
python src/main.py --path "C:\Music" --recursive --output report.csv

# Solo formatos específicos
python src/main.py --path "C:\Music" --formats mp3 flac

# Modo verbose
python src/main.py --path "C:\Music" --verbose
```

## Cómo funciona

El programa utiliza análisis espectral para detectar:

1. **Frecuencia de corte**: Los archivos comprimidos tienen un límite en las frecuencias altas
2. **Artefactos de compresión**: Patrones característicos de compresión lossy
3. **Rango dinámico**: Diferencia entre las partes más suaves y más fuertes
4. **Metadatos vs contenido real**: Compara lo que dice el archivo vs lo que contiene

## Estructura del Proyecto

```
fake-music-hunter/
├── src/
│   ├── main.py         # Punto de entrada CLI
│   ├── scanner.py      # Escaneo de directorios
│   ├── analyzer.py     # Análisis espectral
│   ├── detector.py     # Detección de fake
│   ├── reporter.py     # Generación de reportes
│   └── config.py       # Configuración
├── tests/              # Tests unitarios
├── output/             # Reportes generados
└── requirements.txt
```

## Licencia

MIT

## Autor

pedrit01
