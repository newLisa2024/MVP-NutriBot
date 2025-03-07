import os
from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv
from db import init_db
from bot import create_conv_handler, create_ask_handler
from reminders import start_reminders

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

def main():
    # Инициализируем базу данных
    init_db()

    # Создаем приложение Telegram-бота
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Регистрируем обработчики (регистрация, /ask и т.д.)
    conv_handler = create_conv_handler()
    if conv_handler:
        app.add_handler(conv_handler)
    ask_handler = create_ask_handler()
    app.add_handler(ask_handler)

    # Запускаем напоминания о питье воды
    start_reminders(app)

    # Запускаем бота
    app.run_polling()

if __name__ == "__main__":
    main()

