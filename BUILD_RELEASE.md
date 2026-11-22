# Guía de Compilación de Fake Music Hunter

## Crear Release Ejecutable para Windows

> **Nota (v2.1):** el build no cambia. `src/main.py` solo usa el núcleo de análisis (`src/core/`) y nunca importa la parte web (`src/web/`), así que PyInstaller no incluye FastAPI ni sus dependencias. Basta con instalar `requirements.txt` en el venv.

### ⚠️ IMPORTANTE: Usar el Python del Entorno Virtual

PyInstaller **DEBE** ejecutarse con el Python del entorno virtual donde están instaladas todas las dependencias. Si usas solo `python`, puede ejecutarse el Python del sistema que no tiene las librerías necesarias.

### Paso a Paso: Compilación con PyInstaller

**1. Instala PyInstaller en el entorno virtual:**
```powershell
# Asegúrate de estar en el directorio del workspace
cd C:\Users\pedjl\OneDrive\WorkSpace

# Instala PyInstaller en el venv
& .\venv\Scripts\python.exe -m pip install pyinstaller
```

**2. Compila el ejecutable usando RUTAS ABSOLUTAS:**

**OPCIÓN A - Usando el ejecutable Python del venv (RECOMENDADO):**
```powershell
# Desde cualquier ubicación
& "C:\Users\pedjl\OneDrive\WorkSpace\.venv\Scripts\python.exe" -m PyInstaller --onefile --name fake-music-hunter "C:\Users\pedjl\OneDrive\WorkSpace\fake-music-hunter\src\main.py" --noconfirm --workpath "C:\Users\pedjl\OneDrive\WorkSpace\fake-music-hunter\build" --distpath "C:\Users\pedjl\OneDrive\WorkSpace\fake-music-hunter\dist"
```

**OPCIÓN B - Desde el directorio del proyecto:**
```powershell
# Cambiar al directorio del proyecto
cd C:\Users\pedjl\OneDrive\WorkSpace\fake-music-hunter

# Compilar con el Python del venv
& "C:\Users\pedjl\OneDrive\WorkSpace\.venv\Scripts\python.exe" -m PyInstaller --onefile --name fake-music-hunter src\main.py --noconfirm
```

**3. Resultado:**
- Ejecutable generado en: `dist\fake-music-hunter.exe`
- Tamaño aproximado: **200-250 MB**
- Tiempo de compilación: **5-10 minutos**
- Incluye: Python 3.13 + las dependencias de `requirements.txt` (librosa, numpy, scipy, mutagen, rich, click, soundfile)

### ❌ Problemas Comunes y Soluciones

#### Error: "No module named 'click'" al ejecutar el .exe
**Causa:** PyInstaller usó el Python del sistema en lugar del venv.

**Solución:** Usa la ruta completa al Python del venv:
```powershell
& "C:\Users\pedjl\OneDrive\WorkSpace\.venv\Scripts\python.exe" -m PyInstaller ...
```

#### Error: "Script file 'src\main.py' does not exist"
**Causa:** El directorio actual de PowerShell no es el del proyecto.

**Solución:** Usa rutas absolutas (ver OPCIÓN A arriba) o cambia al directorio correcto:
```powershell
cd C:\Users\pedjl\OneDrive\WorkSpace\fake-music-hunter
```

#### La compilación se interrumpe o falla
**Solución:** Limpia archivos anteriores antes de compilar:
```powershell
Remove-Item -Recurse -Force build, dist, *.spec -ErrorAction SilentlyContinue
```

#### La compilación se interrumpe o falla
**Solución:** Limpia archivos anteriores antes de compilar:
```powershell
Remove-Item -Recurse -Force build, dist, *.spec -ErrorAction SilentlyContinue
```

#### Verificar que el venv tiene las dependencias
```powershell
& "C:\Users\pedjl\OneDrive\WorkSpace\.venv\Scripts\python.exe" -c "import click; print('Click OK')"
& "C:\Users\pedjl\OneDrive\WorkSpace\.venv\Scripts\python.exe" -c "import librosa; print('Librosa OK')"
```

### 🎯 Comando de Compilación Optimizado (Copia y Pega)

Este comando único limpia, compila y muestra el resultado:

```powershell
cd C:\Users\pedjl\OneDrive\WorkSpace\fake-music-hunter ; Remove-Item -Recurse -Force build, dist, *.spec -ErrorAction SilentlyContinue ; Write-Host "`n=== COMPILANDO FAKE MUSIC HUNTER V2.0 ===" -ForegroundColor Cyan ; & "C:\Users\pedjl\OneDrive\WorkSpace\.venv\Scripts\python.exe" -m PyInstaller --onefile --name fake-music-hunter src\main.py --noconfirm ; if (Test-Path "dist\fake-music-hunter.exe") { Write-Host "`nCOMPILACION EXITOSA!" -ForegroundColor Green ; Get-Item dist\fake-music-hunter.exe | Select-Object Name, @{Name="Tamaño (MB)";Expression={[math]::Round($_.Length/1MB, 2)}} | Format-List }
```

## 🧪 Testing del Ejecutable

Una vez compilado, prueba el ejecutable:

```powershell
# Ver ayuda
.\dist\fake-music-hunter.exe --help

# Analizar una carpeta
.\dist\fake-music-hunter.exe analyze "C:\Music\Albums"

# Análisis con salida JSON
.\dist\fake-music-hunter.exe analyze "C:\Music" --output report.json --format json

# Análisis con salida CSV
.\dist\fake-music-hunter.exe analyze "C:\Music" --output report.csv --format csv
```

## 📦 Distribución del Release

### Crear Paquete ZIP para Distribución

```powershell
# Crear carpeta de release
New-Item -ItemType Directory -Force -Path release

# Copiar ejecutable y documentación
Copy-Item dist\fake-music-hunter.exe release\
Copy-Item README.md release\
Copy-Item LICENSE release\

# Crear ZIP
Compress-Archive -Path release\* -DestinationPath fake-music-hunter-v2.0-windows-x64.zip
```

### Publicar en GitHub Releases

Las etiquetas siguen el formato `Version-X.Y.Z` y apuntan a `main`. Las notas de la release son la entrada de esa versión en `CHANGELOG.md`.

```bash
# 1. Pasar develop a main
git checkout main
git merge --no-ff develop
git push origin main

# 2. Crear y subir la etiqueta
git tag -a Version-2.1.0 -m "Fake Music Hunter 2.1.0 - Docker e interfaz web"
git push origin Version-2.1.0

# 3. Crear la release con las notas (y el .exe de Windows si se ha compilado)
gh release create Version-2.1.0 --title "Fake Music Hunter 2.1.0" --notes-file RELEASE_NOTES.md \
  fake-music-hunter-v2.1.0-windows.exe
```

Las notas de cada versión están en `RELEASE_NOTES.md` (bloque de instalación + entrada del CHANGELOG): úsalo como `--notes-file`.

### Publicar la imagen en GHCR

Requiere un token con `write:packages` (el de `gh` sirve si lo tiene: `gh auth refresh -s write:packages`).

```bash
gh auth token | docker login ghcr.io -u pedrit01 --password-stdin
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/pedrit01/fake-music-hunter:2.1.0 \
  -t ghcr.io/pedrit01/fake-music-hunter:latest \
  --push .
```

La primera vez que se publica, el paquete es privado: hazlo público en GitHub → Packages → fake-music-hunter → Package settings → Change visibility.

## 📊 Información Técnica del Ejecutable

### Tamaños Estimados
- **Ejecutable único (.exe):** 200-250 MB
- **ZIP de distribución:** 100-120 MB (comprimido)

### Contenido Empaquetado
El ejecutable incluye:
- ✅ Python 3.13.9 runtime
- ✅ librosa 0.11.0 (análisis de audio)
- ✅ numpy 2.3.4 + scipy 1.16.3 (procesamiento numérico)
- ✅ click 8.3.1 (CLI)
- ✅ rich 14.2.0 (interfaz de consola)
- ✅ mutagen 1.47.0 (metadatos de audio)
- ✅ soundfile 0.13.1 (lectura de audio)
- ✅ numba 0.62.1 (optimización JIT)

### Requisitos del Sistema Cliente
- **SO:** Windows 10/11 (64-bit)
- **RAM:** Mínimo 2 GB, recomendado 4 GB
- **Espacio:** ~300 MB libres
- **No requiere:** Python, dependencias, o instalación

## 🔧 Compilación Avanzada

### Reducir Tamaño del Ejecutable

Excluir módulos no usados:

```powershell
& "C:\Users\pedjl\OneDrive\WorkSpace\.venv\Scripts\python.exe" -m PyInstaller --onefile --name fake-music-hunter src\main.py --exclude-module matplotlib --exclude-module tkinter --exclude-module PyQt5 --exclude-module notebook --exclude-module jupyter --exclude-module pytest --noconfirm
```

### Usar UPX para Comprimir (Opcional)

1. Descarga UPX: https://github.com/upx/upx/releases
2. Extrae en `C:\upx`
3. Compila con UPX:

```powershell
& "C:\Users\pedjl\OneDrive\WorkSpace\.venv\Scripts\python.exe" -m PyInstaller --onefile --name fake-music-hunter src\main.py --upx-dir=C:\upx --noconfirm
```

Esto puede reducir el tamaño en ~30-40% (de 250 MB a 150-180 MB).

## 📝 Notas Adicionales

- La primera ejecución del .exe puede tardar unos segundos mientras descomprime internamente
- El ejecutable es portable - puedes copiarlo a USB y ejecutarlo en cualquier PC
- Para debugging, elimina `--console` del comando PyInstaller para crear una app sin ventana de consola
- Los archivos `.spec` generados pueden reutilizarse para compilaciones futuras más rápidas
