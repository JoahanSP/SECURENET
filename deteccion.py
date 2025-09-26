import os
import logging
from deepface import DeepFace
from utils import ensure_dir
from config import Config
from database import FaceDatabase

# Configuración
logger = logging.getLogger("Deteccion")
ensure_dir(Config.AUTHORIZED_DIR)

# Base de datos de rostros
face_db = FaceDatabase()

# Cargar rostros autorizados
authorized_faces = []

def load_authorized_faces():
    """Carga los rostros autorizados desde la base de datos"""
    global authorized_faces
    try:
        faces = face_db.get_all_faces()
        authorized_faces = [name for name, _ in faces]
        logger.info(f"Rostros autorizados cargados: {len(authorized_faces)}")
    except Exception as e:
        logger.error(f"Error cargando rostros autorizados: {e}")

def detect_intruder(image_path):
    """Detecta si la persona es un intruso o autorizada"""
    try:
        if not os.path.exists(image_path):
            logger.error(f"Imagen no encontrada: {image_path}")
            return False, None

        # Usamos DeepFace para buscar coincidencias en la carpeta de autorizados
        result = DeepFace.find(
            img_path=image_path,
            db_path=Config.AUTHORIZED_DIR,
            enforce_detection=False
        )

        if isinstance(result, list) and len(result) > 0 and not result[0].empty:
            # Persona autorizada encontrada
            best_match = result[0].iloc[0]
            name = os.path.splitext(os.path.basename(best_match["identity"]))[0]
            logger.info(f"Visitante autorizado detectado: {name}")
            return False, name
        else:
            logger.warning("Intruso detectado")
            return True, None

    except Exception as e:
        logger.error(f"Error en detección: {e}")
        return False, None

def add_authorized_face(image_path, name):
    """Agrega un nuevo rostro autorizado"""
    try:
        if not os.path.exists(image_path):
            logger.error("La imagen no existe para agregar autorizado")
            return False

        # Guardar en base de datos (solo ruta + nombre)
        success = face_db.add_face(name, b"", image_path)  # encoding vacío porque DeepFace no usa el mismo sistema
        if success:
            authorized_faces.append(name)
            logger.info(f"Rostro autorizado agregado: {name}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error agregando rostro autorizado: {e}")
        return False

# Cargar rostros al inicio
load_authorized_faces()
