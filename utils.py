import os
from datetime import datetime
from config import Config
import logging

logger = logging.getLogger("Utils")

def timestamp_filename(original_name):
    """Genera un nombre de archivo con timestamp para evitar sobreescrituras"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_name = "".join(c for c in original_name if c.isalnum() or c in ('-', '_', '.'))
        return f"{timestamp}_{safe_name}"
    except Exception as e:
        logger.error(f"Error generando nombre de archivo: {e}")
        return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_image.jpg"

def ensure_dir(directory):
    """Crea la carpeta si no existe"""
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Directorio creado: {directory}")
    except Exception as e:
        logger.error(f"Error creando directorio {directory}: {e}")
        raise

def cleanup_old_files(directory, max_files=1000):
    """Elimina archivos antiguos si hay demasiados"""
    try:
        if os.path.exists(directory):
            files = sorted([os.path.join(directory, f) for f in os.listdir(directory)], 
                          key=os.path.getctime)
            if len(files) > max_files:
                for file_to_remove in files[:-max_files]:
                    os.remove(file_to_remove)
                    logger.info(f"Archivo antiguo eliminado: {file_to_remove}")
    except Exception as e:
        logger.error(f"Error en limpieza de archivos: {e}")