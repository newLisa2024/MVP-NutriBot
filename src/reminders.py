import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db import get_all_users


async def send_water_reminder(app):
    """Отправляет напоминание о питье воды всем зарегистрированным пользователям."""
    users = get_all_users()  # Получаем список telegram_id
    for user_id in users:
        try:
            await app.bot.send_message(chat_id=user_id, text="Не забудь выпить воды!")
        except Exception as e:
            print(f"Ошибка при отправке напоминания пользователю {user_id}: {e}")


def start_reminders(app):
    """
    Создает и запускает планировщик APScheduler, который каждые 1 минут отправляет напоминания.
    Для тестирования интервал уменьшен до 1 минуты.
    """
    try:
        # Попытка получить уже запущенный event loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Если нет, создаем новый и устанавливаем его как текущий
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    scheduler = AsyncIOScheduler(event_loop=loop)
    scheduler.add_job(send_water_reminder, 'interval', hours=2, args=[app])
    scheduler.start()

