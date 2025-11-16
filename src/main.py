"""
Punto de entrada principal para Fake Music Hunter
"""

import click
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from src.scanner import AudioScanner
from src.analyzer import AudioAnalyzer
from src.detector import FakeDetector
from src.reporter import Reporter
from src.config import SUPPORTED_FORMATS


@click.command()
@click.option('--path', '-p', required=True, type=click.Path(exists=True),
              help='Ruta del directorio a escanear')
@click.option('--recursive/--no-recursive', '-r', default=True,
              help='Escanear subdirectorios recursivamente (default: True)')
@click.option('--formats', '-f', multiple=True,
              help='Formatos a analizar (ej: -f mp3 -f flac). Default: todos')
@click.option('--output', '-o', type=click.Path(),
              help='Archivo de salida para el reporte CSV')
@click.option('--json', '-j', type=click.Path(),
              help='Archivo de salida para el reporte JSON')
@click.option('--verbose', '-v', is_flag=True,
              help='Mostrar información detallada de todos los archivos')
def main(path: str, recursive: bool, formats: tuple, output: str, json: str, verbose: bool):
    """
    🎵 Fake Music Hunter - Detector de archivos de audio falsos
    
    Analiza archivos de audio para detectar si han sido convertidos
    desde formatos de menor calidad.
    """
    # Inicializar reporter
    reporter = Reporter(verbose=verbose)
    reporter.print_header()
    
    # Preparar formatos
    selected_formats = list(formats) if formats else SUPPORTED_FORMATS
    
    # Crear scanner
    scanner = AudioScanner(path, recursive=recursive, formats=selected_formats)
    
    # Obtener lista de archivos
    files = list(scanner.scan())
    total_files = len(files)
    
    if total_files == 0:
        reporter.console.print(f"\n[yellow]No se encontraron archivos de audio en: {path}[/yellow]")
        return
    
    reporter.print_scan_info(path, total_files)
    reporter.console.print("🔍 Analizando archivos...\n")
    
    # Analizar archivos con barra de progreso
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=reporter.console
    ) as progress:
        
        task = progress.add_task("[cyan]Procesando...", total=total_files)
        
        for file_path in files:
            # Actualizar progreso
            progress.update(task, description=f"[cyan]Analizando: {file_path.name}")
            
            # Analizar archivo
            analyzer = AudioAnalyzer(file_path)
            analysis_results = analyzer.analyze()
            
            # Detectar fake
            classification, reason = FakeDetector.detect(analysis_results)
            
            # Añadir resultados
            result = {
                **analysis_results,
                'classification': classification,
                'reason': reason
            }
            
            reporter.add_result(result)
            
            # Imprimir resultado individual
            reporter.print_result(result)
            
            # Avanzar progreso
            progress.advance(task)
    
    # Imprimir resumen
    reporter.print_summary()
    
    # Exportar reportes
    if output:
        reporter.export_csv(output)
    
    if json:
        reporter.export_json(json)
    
    # Si no se especificó output, preguntar si quiere guardar
    if not output and not json:
        reporter.console.print()


if __name__ == '__main__':
    main()
