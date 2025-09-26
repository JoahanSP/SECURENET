# app.py (versión con login)
from flask import Flask, request, render_template, send_from_directory, jsonify, redirect, url_for, session
import logging
import os
from config import Config
from security import require_api_key, allowed_file
from almacenamiento import save_image, move_image, delete_image
from deteccion import detect_intruder, add_authorized_face, load_authorized_faces, face_db
from alertas import queue_alert, button_callback, handle_text_message
from telegram.ext import Updater, CallbackQueryHandler, MessageHandler, Filters
from logging_config import setup_logging
from utils import ensure_dir
import auth  # nuestro módulo de autenticación

# Setup
setup_logging()
logger = logging.getLogger("Servidor")
app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_FILE_SIZE
app.secret_key = Config.SECRET_KEY

# Asegurar carpetas
ensure_dir(Config.UPLOAD_FOLDER)
ensure_dir(Config.INTRUDERS_DIR)
ensure_dir(Config.NO_DETECTION_DIR)
ensure_dir(Config.AUTHORIZED_DIR)

# ---------- Helper: login_required ----------
from functools import wraps
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("username"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated

# ---------- Rutas de autenticación ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        if auth.verify_user(username, password):
            session['username'] = username
            logger.info(f"Usuario logueado: {username}")
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")
    return render_template("login.html", error=None)

@app.route("/logout")
def logout():
    user = session.pop("username", None)
    logger.info(f"Usuario desconectado: {user}")
    return redirect(url_for("login"))

# ---------- Index (dashboard) protegido ----------
@app.route("/", methods=["GET"])
@login_required
def index():
    return render_template("index.html", username=session.get("username"))

# ---------- Upload (sigue protegido con API key) ----------
@app.before_request
def check_file_size():
    if request.method == 'POST' and request.content_length and request.content_length > Config.MAX_FILE_SIZE:
        logger.warning("Intento de subida de archivo demasiado grande")
        return jsonify({"error": "Archivo demasiado grande"}), 413

@app.route("/upload", methods=["POST"])
@require_api_key
def upload():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No se envió ninguna imagen"}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "Nombre de archivo vacío"}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": "Tipo de archivo no permitido"}), 400

        filepath = save_image(file, Config.NO_DETECTION_DIR)
        logger.info(f"Imagen recibida: {os.path.basename(filepath)}")

        intruder, name = detect_intruder(filepath)
        if intruder:
            final_path = move_image(filepath, Config.INTRUDERS_DIR)
            queue_alert(final_path)
            logger.warning(f"Intruso detectado: {os.path.basename(final_path)}")
            return jsonify({
                "status": "intruder_detected",
                "message": "Intruso detectado y notificado"
            }), 200
        else:
            message = "No se detectaron rostros" if not name else f"Visitante autorizado: {name}"
            logger.info(f"Detección exitosa: {message}")
            return jsonify({
                "status": "authorized" if name else "no_faces",
                "message": message,
                "name": name
            }), 200

    except Exception as e:
        logger.error(f"Error en endpoint /upload: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

# ---------- Endpoints de lista (igual que antes) ----------
@app.route("/api/alerts", methods=["GET"])
@login_required
def api_alerts():
    try:
        files = os.listdir(Config.INTRUDERS_DIR)
        return jsonify(files)
    except Exception as e:
        logger.error(f"Error listando alertas: {e}")
        return jsonify([]), 500

@app.route("/api/images", methods=["GET"])
@login_required
def api_images():
    try:
        files = os.listdir(Config.NO_DETECTION_DIR)
        return jsonify(files)
    except Exception as e:
        logger.error(f"Error listando imágenes: {e}")
        return jsonify([]), 500

@app.route("/api/authorized-faces", methods=["GET"])
@login_required
def get_authorized_faces():
    try:
        faces = []
        for filename in os.listdir(Config.AUTHORIZED_DIR):
            name = os.path.splitext(filename)[0]
            faces.append({
                "name": name,
                "image_url": f"/authorized/{filename}",
                "filename": filename
            })
        return jsonify(faces)
    except Exception as e:
        logger.error(f"Error obteniendo rostros autorizados: {e}")
        return jsonify({"error": "Error interno"}), 500

@app.route("/api/authorized-faces", methods=["POST"])
@require_api_key
def add_authorized_face_api():
    try:
        if 'image' not in request.files or 'name' not in request.form:
            return jsonify({"error": "Faltan datos: image y name requeridos"}), 400
        file = request.files['image']
        name = request.form['name'].strip()
        if not name:
            return jsonify({"error": "Nombre no puede estar vacío"}), 400
        filepath = save_image(file, Config.AUTHORIZED_DIR)
        if add_authorized_face(filepath, name):
            return jsonify({
                "status": "success",
                "message": f"Rostro de {name} agregado correctamente"
            })
        else:
            delete_image(filepath)
            return jsonify({"error": "No se detectó rostro en la imagen"}), 400
    except Exception as e:
        logger.error(f"Error agregando rostro autorizado: {e}")
        return jsonify({"error": "Error interno"}), 500

@app.route("/api/authorized-faces/<name>", methods=["DELETE"])
@require_api_key
def delete_authorized_face(name):
    try:
        if face_db.delete_face(name):
            return jsonify({"status": "success", "message": f"{name} eliminado"})
        return jsonify({"error": "No se encontró el rostro"}), 404
    except Exception as e:
        logger.error(f"Error eliminando rostro: {e}")
        return jsonify({"error": "Error interno"}), 500

# ---------- Rutas para servir archivos ----------
@app.route("/alerts/<filename>")
@login_required
def alert_file(filename):
    return send_from_directory(Config.INTRUDERS_DIR, filename)

@app.route("/authorized/<filename>")
@login_required
def authorized_file(filename):
    return send_from_directory(Config.AUTHORIZED_DIR, filename)

@app.route("/images/<filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(Config.NO_DETECTION_DIR, filename)

@app.route("/api/stats")
@login_required
def api_stats():
    try:
        stats = {
            "authorized_faces": len(os.listdir(Config.AUTHORIZED_DIR)),
            "intruder_alerts": len(os.listdir(Config.INTRUDERS_DIR)),
            "total_uploads": len(os.listdir(Config.NO_DETECTION_DIR))
        }
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return jsonify({"error": "Error interno"}), 500

# Error handlers (igual que antes)
@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "Archivo demasiado grande"}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Error interno del servidor"}), 500

# Bot telegram (igual)
def setup_telegram_bot():
    try:
        updater = Updater(token=Config.TELEGRAM_TOKEN)
        dispatcher = updater.dispatcher
        dispatcher.add_handler(CallbackQueryHandler(button_callback))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text_message))
        updater.start_polling()
        logger.info("Bot de Telegram iniciado correctamente")
        return updater
    except Exception as e:
        logger.error(f"Error iniciando bot de Telegram: {e}")
        return None

if __name__ == "__main__":
    auth.init_db()
    load_authorized_faces()
    telegram_updater = setup_telegram_bot()
    try:
        logger.info(f"Iniciando servidor en {Config.HOST}:{Config.PORT}")
        app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Servidor detenido por el usuario")
    except Exception as e:
        logger.error(f"Error iniciando servidor: {e}")
    finally:
        if telegram_updater:
            telegram_updater.stop()
