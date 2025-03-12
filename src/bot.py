import os
import logging
from telegram import Update, ReplyKeyboardMarkup, InputFile
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
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
from nutrition_agent import generate_nutrition_plan
from src.generate_images import generate_recipe_image
from keyboards import get_main_keyboard

logger = logging.getLogger(__name__)

# Состояния регистрации
NAME, AGE, WEIGHT, GOAL, DISEASES, ALLERGIES = range(6)


# --- ФУНКЦИИ РЕГИСТРАЦИИ ---

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if is_user_registered(user.id):
            response_text = "✅ Вы уже зарегистрированы! Выберите команду:"
        else:
            response_text = "👋 Привет! Давай пройдём регистрацию.\nКак тебя зовут?"
            context.user_data["registration_step"] = "NAME"

        if update.message:
            await update.message.reply_text(response_text, reply_markup=get_main_keyboard())
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(response_text, reply_markup=get_main_keyboard())

        return NAME if "регистрацию" in response_text else ConversationHandler.END

    except Exception as e:
        logger.error(f"Ошибка регистрации: {str(e)}")
        error_text = "❌ Ошибка регистрации"
        if update.message:
            await update.message.reply_text(error_text)
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.message.edit_text(error_text)
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

    reply_kb = [
        ["Похудение", "Набор массы"],
        ["Поддержание здоровья", "Помощь"]
    ]

    await update.message.reply_text(
        "🎯 Выберите цель (или нажмите 'Помощь'):",
        reply_markup=ReplyKeyboardMarkup(reply_kb, one_time_keyboard=True, resize_keyboard=True)
    )
    return GOAL


async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goal = update.message.text.strip()
    if goal.lower() == "помощь":
        await update.message.reply_text("Выберите нужную команду:", reply_markup=get_main_keyboard())
        return GOAL

    if goal not in ["Похудение", "Набор массы", "Поддержание здоровья"]:
        await update.message.reply_text("⚠️ Выберите цель из списка или нажмите 'Помощь'!")
        return GOAL

    context.user_data['goal'] = goal
    await update.message.reply_text("🏥 Есть ли хронические заболевания? Если нет, напишите 'нет'")
    return DISEASES


async def get_diseases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['diseases'] = update.message.text
    await update.message.reply_text("🌡️ Есть ли аллергии на продукты? Если нет, напишите 'нет'")
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
        await update.message.reply_text("🎉 Регистрация завершена! Выберите команду:", reply_markup=get_main_keyboard())
    else:
        await update.message.reply_text("❌ Ошибка сохранения данных")
    return ConversationHandler.END


# --- ФУНКЦИИ КОНСУЛЬТАЦИИ И РЕЦЕПТОВ ---

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        question = " ".join(context.args)
        if not question:
            await update.message.reply_text("❓ Задайте вопрос после команды /ask")
            return
        user_id = update.effective_user.id
        user_data = get_user_data(user_id) if is_user_registered(user_id) else None
        answer = get_consultation(question, user_data=user_data)
        await update.message.reply_text(answer)
    except Exception as e:
        logger.error(f"Ошибка /ask: {str(e)}")
        await update.message.reply_text("⚠️ Ошибка обработки запроса")


async def handle_ingredients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        if not is_user_registered(user_id):
            await update.message.reply_text("ℹ️ Сначала пройдите регистрацию (/start)")
            return
        ingredients_text = update.message.text.strip()
        if not ingredients_text:
            await update.message.reply_text("❌ Вы не указали ингредиенты. Пожалуйста, отправьте список.")
            return

        user_data = get_user_data(user_id)
        if "?" in ingredients_text or ingredients_text.lower().startswith(
                ("как", "что", "почему", "какие", "зачем", "кто")
        ):
            answer = get_consultation(ingredients_text, user_data=user_data)
            await update.message.reply_text(answer)
            return

        recipe = generate_recipe_with_openai(ingredients=ingredients_text, user_context=user_data)
        if recipe.startswith("⚠️") or recipe.startswith("❌"):
            await update.message.reply_text(recipe)
            return
        if len(recipe) <= 4000:
            await update.message.reply_text(f"🍳 Рецепт:\n\n{recipe}")
        else:
            await update.message.reply_text("🍳 Рецепт слишком длинный, отправляю частями...")
            chunk_size = 3000
            for i in range(0, len(recipe), chunk_size):
                chunk = recipe[i:i + chunk_size]
                await update.message.reply_text(chunk)
    except Exception as e:
        logger.exception("Ошибка рецепта:")
        await update.message.reply_text("⚠️ Не удалось создать рецепт")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🌟 *Доступные команды:*\n"
        "/start - Регистрация\n"
        "/ask [вопрос] - Консультация\n"
        "/nutrition - Персональный план питания\n"
        "/recipe - Рецепт (с изображением)\n"
        "/help - Помощь\n\n"
        "Или нажмите нужную кнопку на клавиатуре ниже."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


async def nutrition_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_user_registered(user.id):
            await update.message.reply_text("ℹ️ Сначала пройдите регистрацию (/start)")
            return
        user_data = get_user_data(user.id)
        plan = generate_nutrition_plan(user_data)
        await update.message.reply_text(plan, reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Ошибка обработки команды /nutrition: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Не удалось сгенерировать план питания")


def create_visual_prompt(recipe_text: str) -> str:
    """
    Формирует визуальный промпт для генерации изображения.
    Предполагается, что название блюда указано в первой строке рецепта.
    """
    lines = recipe_text.splitlines()
    if lines:
        # Из первой строки извлекаем название блюда, убирая эмодзи и лишние пробелы
        title = lines[0].strip("🍽️ ").strip()
        visual_prompt = (
            f"Фотография аппетитного блюда '{title}', студийное освещение, высокое качество, "
            "яркие цвета, профессиональная подача"
        )
        logger.debug(f"Visual prompt: {visual_prompt}")
        return visual_prompt
    return recipe_text


async def recipe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_user_registered(user.id):
            await update.message.reply_text("ℹ️ Сначала пройдите регистрацию (/start)")
            return
        ingredients_text = update.message.text.strip()
        if not ingredients_text:
            await update.message.reply_text("❌ Вы не указали ингредиенты.")
            return

        user_data = get_user_data(user.id)
        recipe_text = generate_recipe_with_openai(ingredients=ingredients_text, user_context=user_data)

        # Формирование отдельного визуального промпта для генерации изображения
        visual_prompt = create_visual_prompt(recipe_text)

        # Генерация изображения через модуль generate_images (используется визуальный промпт)
        image_path = generate_recipe_image(visual_prompt)

        if image_path:
            with open(image_path, "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=recipe_text,
                    reply_markup=get_main_keyboard()
                )
        else:
            await update.message.reply_text(
                "⚠️ Рецепт готов, но не удалось создать изображение.\n\n" + recipe_text,
                reply_markup=get_main_keyboard()
            )
    except Exception as e:
        logger.error(f"Ошибка обработки команды /recipe: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Ошибка генерации рецепта")


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите команду:", reply_markup=get_main_keyboard())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    command = query.data
    if command == "/start":
        await start_registration(update, context)
    elif command == "/ask":
        await query.message.reply_text("Введите ваш вопрос для консультации:")
    elif command == "/nutrition":
        await nutrition_handler(update, context)
    elif command == "/recipe":
        await query.message.reply_text("Пожалуйста, отправьте список ингредиентов для рецепта:")
    elif command == "/help":
        await help_command(update, context)
    else:
        await query.message.reply_text("⚠️ Неизвестная команда.")


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚠️ Неизвестная команда. Используйте /help или выберите кнопку из меню.")


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


def create_nutrition_handler():
    return CommandHandler("nutrition", nutrition_handler)


def create_recipe_handler():
    return CommandHandler("recipe", recipe_handler)















