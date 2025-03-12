# reminders.py
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import get_all_users

# Настройка логирования
logger = logging.getLogger(__name__)


async def send_water_reminder(app):
    """Отправляет напоминание о воде всем зарегистрированным пользователям"""
    try:
        logger.info("Запущена отправка напоминаний о воде")

        # Получаем список пользователей
        users = get_all_users()
        if not users:
            logger.warning("Нет зарегистрированных пользователей для напоминаний")
            return

        success_count = 0
        fail_count = 0

        for user_id in users:
            try:
                await app.bot.send_message(
                    chat_id=user_id,
                    text="💧 Не забудьте выпить воды! Сохраняйте водный баланс!"
                )
                success_count += 1
                logger.debug(f"Напоминание отправлено пользователю {user_id}")

            except Exception as e:
                fail_count += 1
                logger.error(f"Ошибка отправки пользователю {user_id}: {str(e)}", exc_info=True)

        logger.info(
            f"Напоминания отправлены. Успешно: {success_count}, Неудач: {fail_count}"
        )

    except Exception as e:
        logger.critical(f"Критическая ошибка в send_water_reminder: {str(e)}", exc_info=True)
        raise


def start_reminders(app):
    try:
        logger.info("Инициализация сервиса напоминаний")

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        scheduler = AsyncIOScheduler(event_loop=loop)

        # Отправка напоминания каждые 2 часа только с 8:00 до 20:00
        scheduler.add_job(
            send_water_reminder,
            'cron',
            hour='8-20/2',  # запуск в 8, 10, 12, 14, 16, 18, 20 часов
            args=[app],
            id="water_reminder",
            misfire_grace_time=300
        )

        scheduler.start()
        logger.info("Планировщик напоминаний запущен. Напоминания будут приходить только в дневное время.")

    except Exception as e:
        logger.critical(f"Ошибка инициализации планировщика: {str(e)}", exc_info=True)
        raise
