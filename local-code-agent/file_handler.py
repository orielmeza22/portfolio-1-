"""
Manejador de archivos para leer y analizar código
"""

import os
from pathlib import Path
from typing import Optional, List
from config import WORKING_DIRECTORY


class FileHandler:
    """Clase para manejar operaciones con archivos"""
    
    def __init__(self, working_dir: str = WORKING_DIRECTORY):
        self.working_dir = Path(working_dir).expanduser().resolve()
        
    def read_file(self, filepath: str) -> Optional[str]:
        """
        Leer el contenido de un archivo
        
        Args:
            filepath: Ruta del archivo (relativa o absoluta)
            
        Returns:
            Contenido del archivo o None si hay error
        """
        try:
            # Si es ruta relativa, usar directorio de trabajo
            path = Path(filepath)
            if not path.is_absolute():
                path = self.working_dir / path
            
            if not path.exists():
                return f"Error: El archivo '{filepath}' no existe"
            
            if not path.is_file():
                return f"Error: '{filepath}' no es un archivo"
            
            # Evitar archivos muy grandes (> 1MB)
            if path.stat().st_size > 1024 * 1024:
                return f"Error: El archivo es demasiado grande (> 1MB)"
            
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
                
        except Exception as e:
            return f"Error leyendo archivo: {str(e)}"
    
    def list_files(self, directory: str = ".", pattern: Optional[str] = None) -> List[str]:
        """
        Listar archivos en un directorio
        
        Args:
            directory: Directorio a listar
            pattern: Patrón opcional para filtrar (ej: '*.py')
            
        Returns:
            Lista de rutas de archivos
        """
        try:
            path = Path(directory)
            if not path.is_absolute():
                path = self.working_dir / path
            
            if not path.exists():
                return [f"Error: El directorio '{directory}' no existe"]
            
            files = []
            if pattern:
                files = [str(f) for f in path.glob(pattern)]
            else:
                files = [str(f) for f in path.iterdir() if f.is_file()]
            
            return sorted(files)
            
        except Exception as e:
            return [f"Error: {str(e)}"]
    
    def get_file_info(self, filepath: str) -> dict:
        """
        Obtener información sobre un archivo
        
        Args:
            filepath: Ruta del archivo
            
        Returns:
            Diccionario con información del archivo
        """
        try:
            path = Path(filepath)
            if not path.is_absolute():
                path = self.working_dir / path
            
            if not path.exists():
                return {"error": "Archivo no existe"}
            
            return {
                "name": path.name,
                "path": str(path),
                "size": path.stat().st_size,
                "extension": path.suffix,
                "is_file": path.is_file(),
                "is_dir": path.is_dir()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def file_exists(self, filepath: str) -> bool:
        """Verificar si un archivo existe"""
        path = Path(filepath)
        if not path.is_absolute():
            path = self.working_dir / path
        return path.exists() and path.is_file()
