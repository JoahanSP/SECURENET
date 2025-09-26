import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    UPLOAD_FOLDER = "uploads"
    AUTHORIZED_DIR = "Rostro_autorizados"
    INTRUDERS_DIR = "Ima_Con_Intrusos"
    NO_DETECTION_DIR = "Ima_Sin_deteccion"
    LOG_DIR = "logs"

    MAX_FILE_SIZE = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp'}
    API_KEYS = {
        "esp32_cam_1": os.getenv("API_KEY", "default_api_key_123")
    }

    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Añade SECRET_KEY para sesiones de Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "cambia_esto_por_una_aleatoria_y_segura")
