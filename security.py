from functools import wraps
from flask import request, jsonify
from config import Config
import logging

logger = logging.getLogger("Seguridad")

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key not in Config.API_KEYS.values():
            logger.warning(f"Intento de acceso con API key inválida: {api_key}")
            return jsonify({"error": "API key inválida"}), 401
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """Verifica si la extensión del archivo está permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS