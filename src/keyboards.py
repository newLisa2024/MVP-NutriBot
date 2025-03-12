from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Словарь с промптами для каждой кнопки
BUTTON_PROMPTS = {
    "/start": "👋 Пройдём регистрацию! Введите ваше имя:",
    "/ask": "❓ Введите ваш вопрос для консультации:",
    "/nutrition": "📋 Получите ваш персональный план питания:",
    "/recipe": "🍳 Пожалуйста, отправьте список ингредиентов для рецепта:",
    "/help": "💡 Чем могу помочь? Задайте вопрос или выберите команду."
}

def get_main_keyboard():
    """
    Главное меню в виде inline-кнопок.
    """
    keyboard = [
        [InlineKeyboardButton("Регистрация", callback_data="/start")],
        [InlineKeyboardButton("Консультация", callback_data="/ask")],
        [InlineKeyboardButton("План питания", callback_data="/nutrition")],
        [InlineKeyboardButton("Рецепт", callback_data="/recipe")],
        [InlineKeyboardButton("Помощь", callback_data="/help")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_prompt_for_button(button_command):
    """
    Возвращает текстовое приглашение для заданной команды кнопки.
    """
    return BUTTON_PROMPTS.get(button_command, "")



