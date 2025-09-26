# auth.py
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def create_user(username: str, password: str) -> bool:
    """Crea un usuario con contraseña hasheada. Devuelve True si se creó."""
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        ph = generate_password_hash(password)
        conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, ph))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error creando usuario:", e)
        return False

def verify_user(username: str, password: str) -> bool:
    """Verifica credenciales."""
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return False
        return check_password_hash(row[0], password)
    except Exception as e:
        print("Error verificando usuario:", e)
        return False

if __name__ == "__main__":
    # ejemplo: crear usuario admin (ejecuta: python auth.py)
    if create_user("Joahan", "1234"):
        print("Usuario admin creado con contraseña admin123 (cámbiala)")
    else:
        print("No se pudo crear admin (quizá ya existe)")
