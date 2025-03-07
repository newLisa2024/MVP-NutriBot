import os
import logging
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from dotenv import load_dotenv
from db import init_db
from bot import (
    create_conv_handler,
    create_ask_handler,
    create_message_handler,
    create_help_handler,
    unknown_command
)
from reminders import start_reminders

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

def main():
    try:
        # Инициализация базы данных
        init_db()
        logger.info("База данных успешно инициализирована")

        # Создание приложения бота
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        logger.info("Приложение бота создано")

        # Регистрация обработчиков
        handlers = [
            create_conv_handler(),    # Регистрация
            create_ask_handler(),     # /ask
            create_help_handler(),    # /help
            create_message_handler()  # Текстовые сообщения
        ]

        for handler in handlers:
            if handler:
                app.add_handler(handler)
                logger.debug(f"Добавлен обработчик: {handler.__class__.__name__}")

        # Обработчик неизвестных команд
        app.add_handler(MessageHandler(filters.COMMAND, unknown_command))

        # Запуск напоминаний
        start_reminders(app)
        logger.info("Сервис напоминаний активирован")

        # Запуск бота
        logger.info("Запуск бота в режиме polling...")
        app.run_polling()

    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}")
        raise

if __name__ == "__main__":
    main()

