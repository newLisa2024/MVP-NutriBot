import os
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from db import add_user
from consult import get_consultation

# Определяем состояния для многошаговой регистрации
NAME, AGE, WEIGHT, GOAL, DISEASES, ALLERGIES = range(6)

# Функции для регистрации

async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Давай начнем регистрацию. Как тебя зовут?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Сколько тебе лет?")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text
    await update.message.reply_text("Какой у тебя вес?")
    return WEIGHT

async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['weight'] = update.message.text
    await update.message.reply_text("Какова твоя цель (похудение, набор массы, поддержание здоровья)?")
    return GOAL

async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['goal'] = update.message.text
    await update.message.reply_text("Есть ли у тебя заболевания? Если нет, напиши 'нет'.")
    return DISEASES

async def get_diseases(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['diseases'] = update.message.text
    await update.message.reply_text("Есть ли аллергии? Если нет, напиши 'нет'.")
    return ALLERGIES

async def get_allergies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['allergies'] = update.message.text

    # Сохраняем данные пользователя в базу
    add_user(
        telegram_id=update.effective_user.id,
        name=context.user_data.get('name'),
        age=context.user_data.get('age'),
        weight=context.user_data.get('weight'),
        goal=context.user_data.get('goal'),
        diseases=context.user_data.get('diseases'),
        allergies=context.user_data.get('allergies')
    )

    await update.message.reply_text("Регистрация завершена! Спасибо за предоставленные данные.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END

# Обработчик команды /ask для консультаций

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Пожалуйста, задай вопрос после команды /ask.")
        return
    question = " ".join(context.args)
    answer = get_consultation(question)
    await update.message.reply_text(answer)

# Функции для создания обработчиков

def create_conv_handler():
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_registration)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
            DISEASES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_diseases)],
            ALLERGIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_allergies)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    return conv_handler

def create_ask_handler():
    return CommandHandler("ask", ask)



