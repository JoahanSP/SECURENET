import threading
import logging
import os
import time
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler, CallbackContext
from config import Config
from almacenamiento import move_image, delete_image
from deteccion import add_authorized_face, load_authorized_faces

# Configuración
logger = logging.getLogger("Alertas")
bot = Bot(token=Config.TELEGRAM_TOKEN)

# Cola de alertas para procesamiento asíncrono
alert_queue = []
queue_lock = threading.Lock()

def send_telegram_alert(image_path):
    """Envía una alerta a Telegram con opciones de acción"""
    try:
        if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
            logger.error(f"Archivo inválido o vacío: {image_path}")
            return False
        
        with open(image_path, "rb") as f:
            keyboard = [
                [
                    InlineKeyboardButton("✅ Autorizar", callback_data=f"agregar|{image_path}"),
                    InlineKeyboardButton("❌ Intruso", callback_data=f"intruso|{image_path}")
                ],
                [
                    InlineKeyboardButton("👤 Asignar nombre", callback_data=f"nombre|{image_path}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            bot.send_photo(
                chat_id=Config.CHAT_ID,
                photo=f,
                caption="🚨 **Detección de Visitante**\n\n¿Es una persona autorizada?",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        
        logger.info(f"Alerta enviada a Telegram: {os.path.basename(image_path)}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando alerta a Telegram: {e}")
        return False

def alert_worker():
    """Worker que procesa la cola de alertas"""
    while True:
        try:
            with queue_lock:
                if alert_queue:
                    image_path = alert_queue.pop(0)
                else:
                    image_path = None
            
            if image_path:
                send_telegram_alert(image_path)
            else:
                time.sleep(1)  # Esperar si no hay alertas
                
        except Exception as e:
            logger.error(f"Error en el worker de alertas: {e}")
            time.sleep(5)

def queue_alert(image_path):
    """Agrega una alerta a la cola"""
    try:
        with queue_lock:
            alert_queue.append(image_path)
        logger.info(f"Alerta encolada: {os.path.basename(image_path)}")
    except Exception as e:
        logger.error(f"Error encolando alerta: {e}")

def button_callback(update, context):
    """Maneja las interacciones de los botones de Telegram"""
    query = update.callback_query
    query.answer()
    
    try:
        data = query.data
        action, path = data.split("|", 1)
        filename = os.path.basename(path)
        
        if action == "agregar":
            # Mover a autorizados y agregar rostro
            new_path = move_image(path, Config.AUTHORIZED_DIR)
            name = os.path.splitext(filename)[0]
            
            if add_authorized_face(new_path, name):
                query.edit_message_caption(
                    caption=f"✅ **{name}** agregado a autorizados."
                )
            else:
                query.edit_message_caption(
                    caption=f"❌ Error al agregar {name} a autorizados."
                )
                
        elif action == "intruso":
            # Dejar en intrusos
            query.edit_message_caption(
                caption=f"⚠️ **{filename}** marcado como intruso."
            )
            
        elif action == "nombre":
            # Solicitar nombre para el rostro
            context.user_data['pending_face'] = path
            query.edit_message_caption(
                caption=f"👤 Por favor, envía el nombre para **{filename}**"
            )
            
        logger.info(f"Acción realizada: {action} para {filename}")
        
    except Exception as e:
        logger.error(f"Error en callback de Telegram: {e}")
        query.edit_message_caption(caption="❌ Error procesando la solicitud.")

def handle_text_message(update, context):
    """Maneja mensajes de texto para asignar nombres"""
    try:
        if 'pending_face' in context.user_data:
            path = context.user_data['pending_face']
            name = update.message.text.strip()
            
            if name:
                new_path = move_image(path, Config.AUTHORIZED_DIR)
                
                if add_authorized_face(new_path, name):
                    update.message.reply_text(f"✅ **{name}** agregado correctamente.", parse_mode="Markdown")
                else:
                    update.message.reply_text("❌ Error al agregar el rostro.")
            else:
                update.message.reply_text("❌ Nombre inválido.")
            
            # Limpiar estado
            del context.user_data['pending_face']
            
    except Exception as e:
        logger.error(f"Error manejando mensaje de texto: {e}")

# Iniciar worker de alertas en segundo plano
threading.Thread(target=alert_worker, daemon=True).start()
logger.info("Sistema de alertas inicializado")