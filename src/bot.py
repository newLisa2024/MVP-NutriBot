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

# Новые состояния регистрации:
# 0 - NAME, 1 - AGE, 2 - WEIGHT, 3 - HEIGHT, 4 - ACTIVITY, 5 - GOAL, 6 - DISEASES, 7 - ALLERGIES
NAME, AGE, WEIGHT, HEIGHT, ACTIVITY, GOAL, DISEASES, ALLERGIES = range(8)


# --- ФУНКЦИИ РЕГИСТРАЦИИ ---

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start. Если пользователь уже зарегистрирован —
    сразу показывает reply‑клавиатуру. Если нет — начинает процесс регистрации.
    """
    try:
        user = update.effective_user
        if is_user_registered(user.id):
            reply_kb = [
                ["Похудение", "Набор массы"],
                ["Поддержание здоровья", "Помощь"]
            ]
            response_text = "✅ Вы уже зарегистрированы! Выберите команду:"
            if update.message:
                await update.message.reply_text(
                    response_text,
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=reply_kb,
                        one_time_keyboard=False,
                        resize_keyboard=True
                    )
                )
            elif update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.message.edit_text(response_text)
            return ConversationHandler.END
        else:
            response_text = "👋 Привет! Давай пройдём регистрацию.\nКак тебя зовут?"
            context.user_data["registration_step"] = "NAME"
            if update.message:
                await update.message.reply_text(response_text)
            elif update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.message.edit_text(response_text)
            return NAME
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
    await update.message.reply_text("Введите ваш вес в килограммах (например, 70).")
    return WEIGHT


async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    weight = update.message.text.replace(',', '.')
    if not weight.replace('.', '', 1).isdigit():
        await update.message.reply_text("🔢 Некорректный формат веса! Пожалуйста, введите число (например, 70).")
        return WEIGHT
    context.user_data['weight'] = weight
    await update.message.reply_text("Введите ваш рост в сантиметрах (например, 170).")
    return HEIGHT


async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    height = update.message.text.replace(',', '.')
    if not height.replace('.', '', 1).isdigit():
        await update.message.reply_text("🔢 Некорректный формат роста! Пожалуйста, введите число (например, 170).")
        return HEIGHT
    context.user_data['height'] = height
    # Запрос уровня физической активности с выбором варианта
    reply_kb = [
        ["1️⃣ Минимальный (сидячий образ жизни)"],
        ["2️⃣ Низкий (1-2 тренировки в неделю)"],
        ["3️⃣ Средний (3-4 тренировки в неделю)"],
        ["4️⃣ Высокий (5-7 тренировок в неделю)"],
        ["5️⃣ Очень высокий (ежедневные интенсивные тренировки)"]
    ]
    await update.message.reply_text(
        "Какой у вас уровень физической активности? Выберите вариант:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=reply_kb,
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return ACTIVITY


async def get_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    activity = update.message.text.strip()
    allowed_options = [
        "1️⃣ Минимальный (сидячий образ жизни)",
        "2️⃣ Низкий (1-2 тренировки в неделю)",
        "3️⃣ Средний (3-4 тренировки в неделю)",
        "4️⃣ Высокий (5-7 тренировок в неделю)",
        "5️⃣ Очень высокий (ежедневные интенсивные тренировки)"
    ]
    if activity not in allowed_options:
        await update.message.reply_text("Пожалуйста, выберите вариант из предложенных.")
        return ACTIVITY
    context.user_data['activity'] = activity
    # Запрос цели с reply‑клавиатурой
    reply_kb = [
        ["Похудение", "Набор массы"],
        ["Поддержание здоровья", "Помощь"]
    ]
    await update.message.reply_text(
        "🎯 Выберите цель (или нажмите 'Помощь'):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=reply_kb,
            one_time_keyboard=True,
            resize_keyboard=True
        )
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
            height=user_data.get('height'),
            activity=user_data.get('activity'),
            goal=user_data.get('goal'),
            diseases=user_data.get('diseases'),
            allergies=update.message.text
    ):
        reply_kb = [
            ["Похудение", "Набор массы"],
            ["Поддержание здоровья", "Помощь"]
        ]
        await update.message.reply_text(
            "🎉 Регистрация завершена! Выберите команду:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=reply_kb,
                one_time_keyboard=False,
                resize_keyboard=True
            )
        )
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


async def recipe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /recipe. Генерация рецепта и картинки.
    Ожидается, что в сообщении содержится список ингредиентов.
    """
    try:
        if update.message and update.message.text:
            ingredients_text = update.message.text.strip()
        elif update.callback_query:
            await update.callback_query.message.reply_text("Пожалуйста, отправьте список ингредиентов для рецепта:")
            return
        else:
            await update.message.reply_text("❌ Не указаны ингредиенты.")
            return

        if not ingredients_text:
            await update.message.reply_text("❌ Вы не указали ингредиенты.")
            return

        user = update.effective_user
        if not is_user_registered(user.id):
            await update.message.reply_text("ℹ️ Сначала пройдите регистрацию (/start)")
            return

        user_data = get_user_data(user.id)
        recipe_text = generate_recipe_with_openai(ingredients=ingredients_text, user_context=user_data)

        def create_visual_prompt(recipe_text: str) -> str:
            lines = recipe_text.splitlines()
            if lines and lines[0].strip():
                title = lines[0].strip("🍽️ ").strip()
                if not title:
                    title = "блюдо"
            else:
                title = "блюдо"
            visual_prompt = (
                f"Фотография аппетитного блюда '{title}', студийное освещение, высокое качество, "
                "яркие цвета, профессиональная подача"
            )
            logger.debug(f"Visual prompt: {visual_prompt}")
            return visual_prompt

        visual_prompt = create_visual_prompt(recipe_text)
        image_path = generate_recipe_image(visual_prompt)
        logger.info(f"Получен путь к изображению: {image_path}")

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
        if update.message:
            await update.message.reply_text("⚠️ Ошибка генерации рецепта")
        elif update.callback_query:
            await update.callback_query.message.reply_text("⚠️ Ошибка генерации рецепта")


async def handle_ingredients(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка всех текстовых сообщений.
    1) Если установлен флаг для рецепта -> recipe_handler
    2) Если установлен флаг для консультации -> консультация
    3) Если "Помощь" -> inline-клавиатура
    4) Если кнопка "Похудение"/"Набор массы"/"Поддержание здоровья" -> поведение "как раньше"
    5) Если похоже на вопрос -> консультация
    6) Иначе fallback
    """
    try:
        user_id = update.effective_user.id
        if not is_user_registered(user_id):
            await update.message.reply_text("ℹ️ Сначала пройдите регистрацию (/start)")
            return

        user_text = update.message.text.strip()
        if not user_text:
            await update.message.reply_text("❌ Пожалуйста, введите ваш вопрос или воспользуйтесь меню.")
            return

        # 1) Режим рецепта
        if context.user_data.get("awaiting_recipe"):
            context.user_data["awaiting_recipe"] = False
            await recipe_handler(update, context)
            return

        # 2) Режим консультации
        if context.user_data.get("awaiting_consultation"):
            context.user_data["awaiting_consultation"] = False
            user_data = get_user_data(user_id)
            answer = get_consultation(user_text, user_data=user_data)
            await update.message.reply_text(answer)
            return

        # 3) "Помощь"
        if user_text.lower() == "помощь":
            await update.message.reply_text("Выберите нужную команду:", reply_markup=get_main_keyboard())
            return

        # 4) Обработка "Похудение"/"Набор массы"/"Поддержание здоровья"
        if user_text in ["Похудение", "Набор массы", "Поддержание здоровья"]:
            # ТУТ ВОССТАНАВЛИВАЕМ "СТАРОЕ" ПОВЕДЕНИЕ
            # Например, меняем цель пользователя и выдаём рекомендации/рецепты/план
            user_data = get_user_data(user_id)
            user_data["goal"] = user_text  # Допустим, пользователь меняет цель
            # Генерируем новый план питания или краткие рекомендации:
            plan = generate_nutrition_plan(user_data)
            await update.message.reply_text(
                f"Вы выбрали цель: {user_text}\n\n" + plan,
                reply_markup=get_main_keyboard()
            )
            return

        # 5) Если похоже на вопрос
        if "?" in user_text or user_text.lower().startswith(
            ("как", "что", "почему", "какие", "зачем", "кто", "можешь", "посоветуй")
        ):
            user_data = get_user_data(user_id)
            answer = get_consultation(user_text, user_data=user_data)
            await update.message.reply_text(answer)
            return

        # 6) Fallback
        await update.message.reply_text(
            "Я не уверена, что вы хотите сделать. "
            "Если нужна консультация, нажмите кнопку «Консультация» или на кнопку «Помощь». "
            "Чтобы получить рецепт, нажмите «Рецепт» или на кнопку «Помощь»."
        )

    except Exception as e:
        logger.exception("Ошибка обработки текста:")
        await update.message.reply_text("⚠️ Не удалось обработать сообщение")


    except Exception as e:
        logger.exception("Ошибка обработки текста:")
        await update.message.reply_text("⚠️ Не удалось обработать сообщение")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🌟 *Доступные команды:*\n"
        "/start - Регистрация\n"
        "/ask [вопрос] - Консультация\n"
        "/nutrition - Персональный план питания\n"
        "/recipe - Рецепт (с изображением)\n"
        "Или нажмите нужную кнопку на клавиатуре ниже."
    )
    if update.message:
        await update.message.reply_text(help_text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    elif update.callback_query:
        await update.callback_query.message.reply_text(help_text, parse_mode="Markdown", reply_markup=get_main_keyboard())


async def nutrition_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        if not is_user_registered(user.id):
            if update.message:
                await update.message.reply_text("ℹ️ Сначала пройдите регистрацию (/start)")
            elif update.callback_query:
                await update.callback_query.message.reply_text("ℹ️ Сначала пройдите регистрацию (/start)")
            return
        user_data = get_user_data(user.id)
        plan = generate_nutrition_plan(user_data)
        if update.message:
            await update.message.reply_text(plan, reply_markup=get_main_keyboard())
        elif update.callback_query:
            await update.callback_query.message.reply_text(plan, reply_markup=get_main_keyboard())
    except Exception as e:
        logger.error(f"Ошибка обработки команды /nutrition: {e}", exc_info=True)
        if update.message:
            await update.message.reply_text("⚠️ Не удалось сгенерировать план питания")
        elif update.callback_query:
            await update.callback_query.message.reply_text("⚠️ Не удалось сгенерировать план питания")


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите команду:", reply_markup=get_main_keyboard())


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    command = query.data
    if command == "/start":
        await start_registration(update, context)
    elif command == "/ask":
        # Устанавливаем флаг, что следующий текст – это запрос к консультанту
        context.user_data["awaiting_consultation"] = True
        await query.message.reply_text("Введите ваш вопрос для консультации:")
    elif command == "/nutrition":
        await nutrition_handler(update, context)
    elif command == "/recipe":
        context.user_data["awaiting_recipe"] = True
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
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
            ACTIVITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_activity)],
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





















