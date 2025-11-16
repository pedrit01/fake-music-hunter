"""
Módulo para escanear directorios en busca de archivos de audio
"""

import os
from pathlib import Path
from typing import List, Generator
from src.config import SUPPORTED_FORMATS


class AudioScanner:
    """Escanea directorios buscando archivos de audio"""
    
    def __init__(self, root_path: str, recursive: bool = True, formats: List[str] = None):
        """
        Inicializa el escáner
        
        Args:
            root_path: Ruta raíz para comenzar el escaneo
            recursive: Si True, escanea subdirectorios
            formats: Lista de extensiones a buscar (ej: ['.mp3', '.flac'])
        """
        self.root_path = Path(root_path)
        self.recursive = recursive
        self.formats = formats or SUPPORTED_FORMATS
        
        # Asegurar que las extensiones comiencen con punto
        self.formats = [fmt if fmt.startswith('.') else f'.{fmt}' 
                       for fmt in self.formats]
        
        # Convertir a minúsculas para comparación case-insensitive
        self.formats = [fmt.lower() for fmt in self.formats]
    
    def scan(self) -> Generator[Path, None, None]:
        """
        Escanea el directorio y genera rutas de archivos de audio
        
        Yields:
            Path: Ruta de cada archivo de audio encontrado
        """
        if not self.root_path.exists():
            raise FileNotFoundError(f"La ruta no existe: {self.root_path}")
        
        if not self.root_path.is_dir():
            raise NotADirectoryError(f"La ruta no es un directorio: {self.root_path}")
        
        # Usar rglob si es recursivo, glob si no
        pattern = '**/*' if self.recursive else '*'
        
        for file_path in self.root_path.glob(pattern):
            if file_path.is_file():
                # Verificar extensión (case-insensitive)
                if file_path.suffix.lower() in self.formats:
                    yield file_path
    
    def count_files(self) -> int:
        """
        Cuenta el número total de archivos que se escanearán
        
        Returns:
            int: Número de archivos encontrados
        """
        return sum(1 for _ in self.scan())
    
    def get_files_by_format(self) -> dict:
        """
        Agrupa los archivos encontrados por formato
        
        Returns:
            dict: Diccionario con formato como clave y lista de archivos
        """
        files_by_format = {fmt: [] for fmt in self.formats}
        
        for file_path in self.scan():
            ext = file_path.suffix.lower()
            if ext in files_by_format:
                files_by_format[ext].append(file_path)
        
        return files_by_format
