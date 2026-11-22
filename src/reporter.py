"""
Módulo para generar reportes de análisis
"""

from pathlib import Path
from datetime import datetime
from typing import Dict
from rich.console import Console
from src import __version__
from src.core import reports
from src.config import (
    DEFAULT_OUTPUT_DIR, EMOJI_MAP, COLOR_MAP,
    CLASS_LEGITIMATE, CLASS_FAKE, CLASS_SUSPICIOUS, CLASS_ERROR
)


class Reporter:
    """Genera reportes de los resultados del análisis"""
    
    def __init__(self, verbose: bool = False):
        """
        Inicializa el reporter
        
        Args:
            verbose: Si True, muestra información detallada
        """
        self.console = Console(force_terminal=True, legacy_windows=False)
        self.verbose = verbose
        self.results = []
    
    def add_result(self, result: Dict):
        """
        Añade un resultado al reporte
        
        Args:
            result: Diccionario con resultados del análisis y detección
        """
        self.results.append(result)
    
    def print_header(self):
        """Imprime el encabezado del programa"""
        try:
            self.console.print(f"\n🎵 [bold cyan]Fake Music Hunter v{__version__}[/bold cyan]")
        except UnicodeEncodeError:
            self.console.print(f"\n[bold cyan]Fake Music Hunter v{__version__}[/bold cyan]")
        self.console.print("═" * 50)
    
    def print_scan_info(self, path: str, total_files: int):
        """
        Imprime información del escaneo
        
        Args:
            path: Ruta escaneada
            total_files: Número total de archivos encontrados
        """
        self.console.print(f"\n📁 Escaneando: [cyan]{path}[/cyan]")
        self.console.print(f"   Archivos encontrados: [yellow]{total_files:,}[/yellow]\n")
    
    def print_result(self, result: Dict):
        """
        Imprime un resultado individual
        
        Args:
            result: Diccionario con resultados del análisis
        """
        classification = result.get('classification', CLASS_ERROR)
        reason = result.get('reason', 'Sin razón')
        file_name = result.get('file_name', 'Desconocido')
        
        emoji = EMOJI_MAP.get(classification, '❓')
        color = COLOR_MAP.get(classification, 'white')
        
        # Mensaje principal
        if classification == CLASS_LEGITIMATE and not self.verbose:
            # En modo no verbose, solo mostrar fake y sospechosos
            return
        
        self.console.print(f"\n{emoji} [{color}]{classification.upper()}[/{color}]: {file_name}")
        
        if self.verbose:
            # Información detallada
            bitrate = result.get('bitrate')
            cutoff_freq = result.get('cutoff_frequency')
            dynamic_range = result.get('dynamic_range')
            spectral_presence = result.get('spectral_presence')
            
            if bitrate:
                self.console.print(f"   • Bitrate: {bitrate/1000:.0f} kbps")
            if cutoff_freq:
                self.console.print(f"   • Frecuencia de corte: {cutoff_freq:.1f} Hz")
            if spectral_presence is not None:
                self.console.print(f"   • Presencia espectral (18-22kHz): {spectral_presence:.1f}%")
            if dynamic_range:
                self.console.print(f"   • Rango dinámico: {dynamic_range:.1f} dB")
        
        # Razón
        self.console.print(f"   • {reason}")
    
    def print_summary(self):
        """Imprime un resumen estadístico de los resultados"""
        if not self.results:
            self.console.print("\n[yellow]No hay resultados para mostrar[/yellow]")
            return
        
        total = len(self.results)
        legitimate = sum(1 for r in self.results if r.get('classification') == CLASS_LEGITIMATE)
        fake = sum(1 for r in self.results if r.get('classification') == CLASS_FAKE)
        suspicious = sum(1 for r in self.results if r.get('classification') == CLASS_SUSPICIOUS)
        errors = sum(1 for r in self.results if r.get('classification') == CLASS_ERROR)
        
        self.console.print("\n" + "═" * 50)
        self.console.print("\n[bold]RESUMEN:[/bold]")
        self.console.print(f"   Total analizado: [cyan]{total:,}[/cyan]")
        
        if legitimate > 0:
            pct = (legitimate / total) * 100
            self.console.print(f"   [OK] Legitimos: [green]{legitimate:,}[/green] ({pct:.1f}%)")
        
        if fake > 0:
            pct = (fake / total) * 100
            self.console.print(f"   [X] Fake: [red]{fake:,}[/red] ({pct:.1f}%)")
        
        if suspicious > 0:
            pct = (suspicious / total) * 100
            self.console.print(f"   [!] Sospechosos: [yellow]{suspicious:,}[/yellow] ({pct:.1f}%)")
        
        if errors > 0:
            pct = (errors / total) * 100
            self.console.print(f"   [ERR] Errores: [dim red]{errors:,}[/dim red] ({pct:.1f}%)")
    
    def export_csv(self, output_path: str = None):
        """
        Exporta los resultados a CSV

        Args:
            output_path: Ruta del archivo CSV de salida
        """
        if not self.results:
            return

        output_path = self._resolve_output_path(output_path, "csv")
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            reports.to_csv(self.results, csvfile)

        self.console.print(f"\n💾 Reporte guardado: [cyan]{output_path}[/cyan]")

    def export_json(self, output_path: str = None):
        """
        Exporta los resultados a JSON

        Args:
            output_path: Ruta del archivo JSON de salida
        """
        if not self.results:
            return

        output_path = self._resolve_output_path(output_path, "json")
        with open(output_path, 'w', encoding='utf-8') as jsonfile:
            reports.to_json(self.results, jsonfile)

        self.console.print(f"\n💾 Reporte JSON guardado: [cyan]{output_path}[/cyan]")

    @staticmethod
    def _resolve_output_path(output_path: str, extension: str) -> Path:
        """Devuelve la ruta de salida, creando su carpeta si hace falta.

        Sin ruta, genera una con fecha y hora dentro de DEFAULT_OUTPUT_DIR.
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_path = Path(DEFAULT_OUTPUT_DIR) / f"report_{timestamp}.{extension}"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path
