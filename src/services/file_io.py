"""
Servicio de Entrada/Salida (I/O) de Archivos

Proporciona utilidades thread-safe para leer/escribir archivos,
asegurando codificación UTF-8 y manejo de errores centralizado.
"""

import json
import threading
from pathlib import Path
from typing import Dict, Any

from src.services.logger import get_logger

logger = get_logger(__name__)

# --- Candado Global de I/O ---
# Se utiliza un candado (Lock) para prevenir condiciones de carrera
# si múltiples hilos intentan escribir en el mismo archivo (ej. log)
# simultáneamente.
_io_lock = threading.Lock()

def read_file(path: str) -> str:
    """
    Lee el contenido de un archivo de texto de forma segura.

    Args:
        path (str): Ruta al archivo.

    Returns:
        str: Contenido del archivo.
    
    Raises:
        FileNotFoundError: Si el archivo no se encuentra.
        IOError: Si ocurre un error de lectura.
    """
    file_path = Path(path)
    logger.debug(f"Intentando leer el archivo: {file_path.absolute()}")
    
    try:
        with _io_lock:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    except FileNotFoundError:
        logger.error(f"Error de I/O: Archivo no encontrado en {file_path.absolute()}")
        raise
    except IOError as e:
        logger.error(f"Error de I/O al leer {file_path.absolute()}: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error inesperado al leer {file_path.absolute()}: {e}", exc_info=True)
        raise IOError(f"Error al leer {file_path.absolute()}")

def write_json(path: str, data: Dict[str, Any]):
    """
    Escribe un diccionario a un archivo JSON de forma segura.

    Args:
        path (str): Ruta al archivo de salida.
        data (Dict[str, Any]): Datos a serializar.
    
    Raises:
        IOError: Si ocurre un error de escritura.
    """
    file_path = Path(path)
    logger.debug(f"Intentando escribir JSON en: {file_path.absolute()}")

    try:
        # Asegurar que el directorio padre existe
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with _io_lock:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Datos JSON escritos exitosamente en {file_path.absolute()}")
        
    except (IOError, TypeError) as e:
        logger.error(f"Error de I/O al escribir JSON en {file_path.absolute()}: {e}", exc_info=True)
        raise IOError(f"Error al escribir JSON en {file_path.absolute()}")

def append_log(path: str, text: str):
    """
    Añade una línea a un archivo de log de forma segura (thread-safe).

    Args:
        path (str): Ruta al archivo de log.
        text (str): Texto a añadir.
    
    Raises:
        IOError: Si ocurre un error de escritura.
    """
    file_path = Path(path)
    
    try:
        # Asegurar que el directorio padre existe
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with _io_lock:
            with open(file_path, 'a', encoding='utf-8') as f:
                # Añadir timestamp es responsabilidad del llamador (o del logger)
                f.write(f"{text}\n")
                
    except (IOError, OSError) as e:
        # Si falla la escritura del log, lo reportamos (¡sin re-loguear!)
        print(f"[Error de I/O en Log] No se pudo escribir en {file_path.absolute()}: {e}")
        raise IOError(f"Error al añadir al log en {file_path.absolute()}")