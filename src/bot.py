import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from db import (
    add_user,
    is_user_registered,
    get_user_data
)
from consult import get_consultation
from recipes import generate_recipe_with_openai

# Настройка логирования
logger = logging.getLogger(__name__)

# Состояния регистрации
NAME, AGE, WEIGHT, GOAL, DISEASES, ALLERGIES = range(6)

GOAL_KEYBOARD = ReplyKeyboardMarkup(
    [["Похудение", "Набор массы"], ["Поддержание здоровья"]],
    one_time_keyboard=True,
    resize_keyboard=True
)

# Максимальная длина сообщения в Telegram (с запасом)
MAX_TELEGRAM_MSG_LENGTH = 4000


# Обработчики команд
async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if is_user_registered(user.id):
            await update.message.reply_text("✅ Вы уже зарегистрированы!")
            return ConversationHandler.END

        await update.message.reply_text("👋 Привет! Давай пройдем регистрацию.\nКак тебя зовут?")
        return NAME
    except Exception as e:
        logger.error(f"Ошибка регистрации: {str(e)}")
        await update.message.reply_text("❌ Ошибка регистрации")
        return ConversationHandler.END


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("📅 Сколько тебе лет?")
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        await update.message.reply_text("🔢 Пожалуйста, введите число!")
        return AGE
    context.user_data['age'] = update.message.text
    await update.message.reply_text("⚖️ Ваш вес (в кг)?")
    return WEIGHT


async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    weight = update.message.text.replace(',', '.')
    if not weight.replace('.', '', 1).isdigit():
        await update.message.reply_text("🔢 Некорректный формат веса!")
        return WEIGHT
    context.user_data['weight'] = weight
    await update.message.reply_text("🎯 Выберите цель:", reply_markup=GOAL_KEYBOARD)
    return GOAL


async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goal = update.message.text
    if goal not in ["Похудение", "Набор массы", "Поддержание здоровья"]:
        await update.message.reply_text("⚠️ Выберите цель из списка!")
        return GOAL
    context.user_data['goal'] = goal
    await update.message.reply_text("🏥 Есть ли хронические заболевания? Если нет, напишите 'нет'")
    return DISEASES


async def get_diseases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['diseases'] = update.message.text
    await update.message.reply_text("🌡️ Есть ли аллергии? Если нет, напишите 'нет'")
    return ALLERGIES


async def get_allergies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    if add_user(
            telegram_id=update.effective_user.id,
            name=user_data.get('name'),
            age=user_data.get('age'),
            weight=user_data.get('weight'),
            goal=user_data.get('goal'),
            diseases=user_data.get('diseases'),
            allergies=update.message.text
    ):
        await update.message.reply_text("🎉 Регистрация завершена!")
    else:
        await update.message.reply_text("❌ Ошибка сохранения данных")
    return ConversationHandler.END


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        question = " ".join(context.args)
        if not question:
            await update.message.reply_text("❓ Задайте вопрос после команды /ask")
            return

        answer = get_consultation(question)
        await update.message.reply_text(answer)
    except Exception as e:
        logger.error(f"Ошибка /ask: {str(e)}")
        await update.message.reply_text("⚠️ Ошибка обработки запроса")


async def handle_ingredients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        # Проверка регистрации
        if not is_user_registered(user_id):
            await update.message.reply_text("ℹ️ Сначала пройдите регистрацию (/start)")
            return

        # Получаем список ингредиентов и удаляем лишние пробелы
        ingredients_text = update.message.text.strip()
        if not ingredients_text:
            await update.message.reply_text("❌ Вы не указали ингредиенты. Пожалуйста, отправьте список.")
            return

        # Получаем данные пользователя (аллергии, цель и т.д.)
        user_data = get_user_data(user_id)

        # Генерируем рецепт
        recipe = generate_recipe_with_openai(
            ingredients=ingredients_text,
            user_context=user_data
        )

        # Если функция вернула сообщение об ошибке (начинается с ⚠️ или ❌),
        # отправляем его напрямую, без префикса "Рецепт"
        if recipe.startswith("⚠️") or recipe.startswith("❌"):
            await update.message.reply_text(recipe)
            return

        # Проверяем длину итогового текста
        if len(recipe) <= MAX_TELEGRAM_MSG_LENGTH:
            # Если текст короче лимита — отправляем одним сообщением
            await update.message.reply_text(f"🍳 Рецепт:\n\n{recipe}")
        else:
            # Разбиваем на части и отправляем по кусочкам
            await update.message.reply_text("🍳 Рецепт слишком длинный, отправляю частями...")
            chunk_size = 3000  # можно подобрать другое значение
            for i in range(0, len(recipe), chunk_size):
                chunk = recipe[i:i + chunk_size]
                await update.message.reply_text(chunk)

    except Exception as e:
        # Логируем подробную информацию об ошибке со стек-трейсом
        logger.exception("Ошибка рецепта:")
        await update.message.reply_text("⚠️ Не удалось создать рецепт")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🌟 *Доступные команды:*\n"
        "/start - Регистрация\n"
        "/ask [вопрос] - Консультация\n"
        "/help - Помощь\n\n"
        "Просто отправьте список продуктов для получения рецепта!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ Неизвестная команда. Используйте /help")


# Фабрики обработчиков
def create_conv_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_registration)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
            DISEASES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_diseases)],
            ALLERGIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_allergies)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        allow_reentry=True
    )


def create_ask_handler():
    return CommandHandler("ask", ask)


def create_help_handler():
    return CommandHandler("help", help_command)


def create_message_handler():
    return MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ingredients)





