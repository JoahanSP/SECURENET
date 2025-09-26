import sqlite3
import numpy as np
import json
import logging
from config import Config

logger = logging.getLogger("BaseDatos")

class FaceDatabase:
    def __init__(self, db_path="faces.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Inicializa la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS authorized_faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    encoding BLOB NOT NULL,
                    image_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
            logger.info("Base de datos inicializada correctamente")
        except Exception as e:
            logger.error(f"Error inicializando BD: {e}")
    
    def add_face(self, name, encoding, image_path):
        """Agrega un nuevo rostro autorizado"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute(
                "INSERT INTO authorized_faces (name, encoding, image_path) VALUES (?, ?, ?)",
                (name, encoding.tobytes(), image_path)
            )
            conn.commit()
            conn.close()
            logger.info(f"Rostro agregado: {name}")
            return True
        except Exception as e:
            logger.error(f"Error agregando rostro: {e}")
            return False
    
    def get_all_faces(self):
        """Obtiene todos los rostros autorizados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name, encoding FROM authorized_faces")
            faces = []
            for name, encoding_blob in cursor.fetchall():
                encoding = np.frombuffer(encoding_blob, dtype=np.float64)
                faces.append((name, encoding))
            conn.close()
            return faces
        except Exception as e:
            logger.error(f"Error obteniendo rostros: {e}")
            return []
    
    def delete_face(self, name):
        """Elimina un rostro autorizado"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("DELETE FROM authorized_faces WHERE name = ?", (name,))
            conn.commit()
            conn.close()
            logger.info(f"Rostro eliminado: {name}")
            return True
        except Exception as e:
            logger.error(f"Error eliminando rostro: {e}")
            return False