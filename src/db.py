import os
import sqlite3

# Получаем абсолютный путь к корневой директории (на уровень выше src/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DB_DIR, exist_ok=True)

DB_NAME = os.path.join(DB_DIR, "users.db")

def init_db():
    """Создаёт таблицу users, если её ещё нет."""
    print(f"DEBUG (db.py): Инициализация БД по пути: {DB_NAME}")
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
    """Добавляет нового пользователя в базу данных."""
    print(f"DEBUG (db.py): add_user -> telegram_id={telegram_id}, name={name}, age={age}")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (telegram_id, name, age, weight, goal, diseases, allergies)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (telegram_id, name, age, weight, goal, diseases, allergies))
    conn.commit()
    conn.close()

def is_user_registered(telegram_id):
    """Проверяет, зарегистрирован ли пользователь с данным telegram_id."""
    print(f"DEBUG (db.py): is_user_registered -> Проверяем ID {telegram_id}")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        print("DEBUG (db.py): Пользователь найден в БД")
        return True
    else:
        print("DEBUG (db.py): Пользователь не найден в БД")
        return False

def get_all_users():
    """Возвращает список telegram_id всех зарегистрированных пользователей."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]




