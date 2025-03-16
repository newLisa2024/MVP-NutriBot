import os
import sqlite3
import logging
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('database.log'),
        logging.StreamHandler()
    ]
)

# Загрузка переменных окружения
load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DB_DIR, exist_ok=True)

DB_NAME = os.path.join(DB_DIR, "users.db")

# Инициализация шифрования
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    logger.error("ENCRYPTION_KEY not found in .env! Generating new key...")
    ENCRYPTION_KEY = Fernet.generate_key().decode()

cipher = Fernet(ENCRYPTION_KEY.encode())

def fix_padding(token: str) -> str:
    missing_padding = len(token) % 4
    if missing_padding:
        token += '=' * (4 - missing_padding)
    return token

def encrypt_data(data: str) -> str:
    """Шифрует строковые данные перед сохранением в БД"""
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Дешифрует данные из БД"""
    fixed_token = fix_padding(encrypted_data)
    return cipher.decrypt(fixed_token.encode()).decode()

def init_db():
    """Инициализирует базу данных с таблицами users и meals"""
    try:
        logger.info(f"Initializing database at: {DB_NAME}")
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            # Таблица пользователей с новыми полями: height и activity
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    name TEXT,
                    age TEXT,
                    weight TEXT,
                    height TEXT,
                    activity TEXT,
                    goal TEXT,
                    diseases TEXT,
                    allergies TEXT
                )
            ''')

            # Таблица приёмов пищи
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS meals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    meal TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(telegram_id)
                )
            ''')

            conn.commit()
            logger.info("Database tables created successfully")
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise

def add_user(telegram_id: int, name: str, age: str, weight: str,
             height: str, activity: str, goal: str, diseases: str, allergies: str) -> bool:
    """Добавляет нового пользователя с шифрованием данных"""
    try:
        encrypted_data = {
            'age': encrypt_data(age),
            'weight': encrypt_data(weight),
            'height': encrypt_data(height),
            'diseases': encrypt_data(diseases),
            'allergies': encrypt_data(allergies),
            'activity': encrypt_data(activity)
        }
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (
                    telegram_id, name, age, weight, height, activity, goal, diseases, allergies
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                telegram_id,
                name,
                encrypted_data['age'],
                encrypted_data['weight'],
                encrypted_data['height'],
                encrypted_data['activity'],
                goal,
                encrypted_data['diseases'],
                encrypted_data['allergies']
            ))
            conn.commit()
        logger.info(f"User {telegram_id} added successfully")
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"User {telegram_id} already exists")
        return False
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        return False

def is_user_registered(telegram_id: int) -> bool:
    """Проверяет регистрацию пользователя"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE telegram_id=?", (telegram_id,))
            return bool(cursor.fetchone())
    except sqlite3.Error as e:
        logger.error(f"Registration check error: {e}")
        return False

def get_user_data(telegram_id: int) -> dict:
    """Возвращает расшифрованные данные пользователя"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT name, age, weight, height, activity, goal, diseases, allergies 
                FROM users WHERE telegram_id=?
            ''', (telegram_id,))
            result = cursor.fetchone()
            if not result:
                return {}
            decrypted_data = {
                'name': result[0],
                'age': decrypt_data(result[1]),
                'weight': decrypt_data(result[2]),
                'height': decrypt_data(result[3]),
                'activity': decrypt_data(result[4]),
                'goal': result[5],
                'diseases': decrypt_data(result[6]),
                'allergies': decrypt_data(result[7])
            }
            return decrypted_data
    except sqlite3.Error as e:
        logger.error(f"Error getting user data: {e}")
        return {}

def add_meal(telegram_id: int, meal: str) -> bool:
    """Добавляет запись о приёме пищи"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO meals (user_id, meal)
                VALUES (?, ?)
            ''', (telegram_id, meal))
            conn.commit()
        logger.info(f"Meal added for user {telegram_id}")
        return True
    except sqlite3.Error as e:
        logger.error(f"Error adding meal: {e}")
        return False

def get_meals(telegram_id: int, limit: int = 10) -> list:
    """Возвращает последние записи о питании"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT meal, timestamp 
                FROM meals 
                WHERE user_id=?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (telegram_id, limit))
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Error getting meals: {e}")
        return []

def get_all_users() -> list:
    """Возвращает список всех зарегистрированных пользователей"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT telegram_id FROM users")
            return [row[0] for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Error getting users: {e}")
        return []





