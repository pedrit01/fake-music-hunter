# Guía de Pruebas - Fake Music Hunter

Esta guía proporciona instrucciones paso a paso para ejecutar las pruebas del proyecto en tu entorno Windows 11.

## 📋 Requisitos Previos

- Python 3.13+ instalado
- Entorno virtual configurado
- Dependencias instaladas

## 🚀 Configuración Inicial (Solo Primera Vez)

### 1. Activar el Entorno Virtual

```powershell
# Desde el directorio raíz del proyecto
C:/Users/pedjl/OneDrive/WorkSpace/.venv/Scripts/Activate.ps1
```

O usa el atajo:
```powershell
.venv\Scripts\Activate.ps1
```

### 2. Verificar que el Entorno Está Activo

Deberías ver `(.venv)` al inicio de tu prompt de PowerShell:
```
(.venv) PS C:\Users\pedjl\OneDrive\WorkSpace\fake-music-hunter>
```

### 3. Instalar Dependencias (si es necesario)

```powershell
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## 🐳 Ejecutar las Pruebas en Docker (recomendado)

No requiere Python ni dependencias en tu máquina:

```bash
docker build -f docker/dev.Dockerfile -t fmh-dev .
docker run --rm -v "$PWD":/app fmh-dev pytest
```

Solo hay que reconstruir la imagen cuando cambian los `requirements*.txt`; el código se monta en `/app`.

## 🧪 Ejecutar las Pruebas

### Opción 1: Tests Básicos (Recomendado)

Ejecuta todos los tests con salida detallada:

```powershell
python -m pytest -v
```

**Salida esperada:**
```
================================= test session starts ==================================
collected 4 items

tests/test_detector.py::TestFakeDetector::test_detector_methods_exist PASSED      [ 25%]
tests/test_detector.py::TestFakeDetector::test_detect_mp3_fake PASSED             [ 50%]
tests/test_detector.py::TestFakeDetector::test_detect_flac_fake PASSED            [ 75%]
tests/test_detector.py::TestFakeDetector::test_detect_error_no_cutoff PASSED      [100%]

================================== 4 passed in 0.09s ===================================
```

### Opción 2: Tests con Cobertura de Código

Para ver qué porcentaje del código está siendo probado:

```powershell
python -m pytest --cov=src --cov-report=term-missing
```

**Salida esperada:**
```
Name              Stmts   Miss  Cover   Missing
-----------------------------------------------
src\__init__.py       2      0   100%
src\analyzer.py      73     73     0%   5-185
src\config.py        18      0   100%
src\detector.py      64     35    45%   39-47, 51, 59-75, ...
src\main.py          47     47     0%   5-109
src\reporter.py      98     98     0%   5-187
src\scanner.py       30     30     0%   5-79
-----------------------------------------------
TOTAL               332    283    15%
```

### Opción 3: Ejecutar Tests Específicos

Para ejecutar solo un archivo de tests:

```powershell
python -m pytest tests/test_detector.py -v
```

Para ejecutar un test específico:

```powershell
python -m pytest tests/test_detector.py::TestFakeDetector::test_detect_mp3_fake -v
```

### Opción 4: Tests en Modo Continuo (Watch Mode)

Útil durante el desarrollo. Requiere `pytest-watch`:

```powershell
# Instalar pytest-watch (solo primera vez)
python -m pip install pytest-watch

# Ejecutar en modo watch
python -m pytest-watch
```

## 📊 Comandos Útiles Adicionales

### Ver Todos los Tests Disponibles

```powershell
python -m pytest --collect-only
```

### Ejecutar con Más Detalles de Errores

```powershell
python -m pytest -vv
```

### Detener en el Primer Fallo

```powershell
python -m pytest -x
```

### Generar Reporte HTML de Cobertura

```powershell
python -m pytest --cov=src --cov-report=html
```

Luego abre `htmlcov/index.html` en tu navegador.

### Ejecutar Solo Tests que Fallaron la Última Vez

```powershell
python -m pytest --lf
```

## 🔧 Solución de Problemas

### Problema: "pytest: command not found"

**Solución:** Asegúrate de que el entorno virtual está activado y pytest está instalado:
```powershell
python -m pip install pytest
```

### Problema: "ModuleNotFoundError"

**Solución:** Instala las dependencias faltantes:
```powershell
python -m pip install -r requirements.txt
```

### Problema: "No module named 'src'"

**Solución:** Asegúrate de ejecutar pytest desde el directorio raíz del proyecto:
```powershell
cd C:\Users\pedjl\OneDrive\WorkSpace\fake-music-hunter
```

### Problema: Tests fallan con "ImportError"

**Solución:** Verifica que todas las dependencias estén instaladas:
```powershell
python -m pip list
```

## 📝 Agregar Nuevos Tests

### 1. Crear un Nuevo Archivo de Tests

Los archivos de tests deben:
- Estar en el directorio `tests/`
- Empezar con `test_` (ejemplo: `test_analyzer.py`)
- Contener clases que empiecen con `Test` (ejemplo: `TestAnalyzer`)
- Contener funciones que empiecen con `test_` (ejemplo: `test_analyze_mp3`)

### 2. Ejemplo de Test Básico

```python
"""
Tests para el módulo analyzer
"""
import pytest
from src.analyzer import AudioAnalyzer


class TestAudioAnalyzer:
    """Tests para la clase AudioAnalyzer"""
    
    def test_analyzer_initialization(self):
        """Test de inicialización del analizador"""
        analyzer = AudioAnalyzer()
        assert analyzer is not None
```

### 3. Ejecutar los Nuevos Tests

```powershell
python -m pytest -v
```

## 🎯 Flujo de Trabajo Recomendado

### Durante el Desarrollo

1. **Activar el entorno virtual**
   ```powershell
   .venv\Scripts\Activate.ps1
   ```

2. **Hacer cambios en el código**

3. **Ejecutar tests relacionados**
   ```powershell
   python -m pytest tests/test_detector.py -v
   ```

4. **Si todo pasa, ejecutar todos los tests**
   ```powershell
   python -m pytest -v
   ```

5. **Verificar cobertura antes de commit**
   ```powershell
   python -m pytest --cov=src --cov-report=term-missing
   ```

### Antes de Hacer Push

```powershell
# 1. Ejecutar todos los tests
python -m pytest -v

# 2. Verificar cobertura
python -m pytest --cov=src --cov-report=term-missing

# 3. Si todo está OK, hacer commit y push
git add .
git commit -m "Descripción de los cambios"
git push
```

## 📚 Recursos Adicionales

- [Documentación de pytest](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Best Practices for Writing Tests](https://docs.pytest.org/en/latest/goodpractices.html)

---

**Última actualización:** 16 de noviembre de 2025
