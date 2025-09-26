import os
import shutil
from utils import timestamp_filename, ensure_dir, cleanup_old_files
from config import Config
import logging
from security import allowed_file

logger = logging.getLogger("Almacenamiento")

def save_image(file, folder):
    """Guarda una imagen en el directorio especificado"""
    try:
        if not file or file.filename == '':
            raise ValueError("Archivo vacío")
        
        if not allowed_file(file.filename):
            raise ValueError(f"Tipo de archivo no permitido: {file.filename}")
        
        ensure_dir(folder)
        filename = timestamp_filename(file.filename)
        path = os.path.join(folder, filename)
        
        file.save(path)
        
        # Verificar que el archivo se guardó correctamente
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            raise ValueError("Archivo no se guardó correctamente")
        
        logger.info(f"Imagen guardada: {path}")
        
        # Limpieza periódica de archivos antiguos
        cleanup_old_files(folder, max_files=1000)
        
        return path
        
    except Exception as e:
        logger.error(f"Error guardando imagen: {e}")
        raise

def move_image(src_path, dest_folder):
    """Mueve una imagen a otro directorio"""
    try:
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"Archivo origen no existe: {src_path}")
        
        ensure_dir(dest_folder)
        filename = os.path.basename(src_path)
        dest_path = os.path.join(dest_folder, filename)
        
        shutil.move(src_path, dest_path)
        logger.info(f"Imagen movida: {src_path} -> {dest_path}")
        
        return dest_path
        
    except Exception as e:
        logger.error(f"Error moviendo imagen: {e}")
        raise

def delete_image(image_path):
    """Elimina una imagen"""
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            logger.info(f"Imagen eliminada: {image_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error eliminando imagen: {e}")
        return False