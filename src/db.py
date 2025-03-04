import os
import sqlite3

DB_DIR = "data"
os.makedirs(DB_DIR, exist_ok=True)  # Создаем папку data, если её нет

DB_NAME = os.path.join(DB_DIR, "users.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            name TEXT,
            age TEXT,
            weight TEXT,
            goal TEXT,
            diseases TEXT,
            allergies TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(telegram_id, name, age, weight, goal, diseases, allergies):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (telegram_id, name, age, weight, goal, diseases, allergies)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (telegram_id, name, age, weight, goal, diseases, allergies))
    conn.commit()
    conn.close()

