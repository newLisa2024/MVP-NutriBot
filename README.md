
# Бот-Нутрициолог

Telegram-бот «Нутрициолог» предоставляет персонализированные рекомендации по питанию, генерирует индивидуальные планы питания и рецепты блюд (с визуализацией через DALL·E API), а также предлагает консультации по вопросам нутрициологии. Бот использует современные технологии искусственного интеллекта и шифрования для защиты персональных данных пользователей.

## Функциональные возможности

- **Регистрация пользователей:**  
  Автоматический сбор персональных данных (имя, возраст, вес, рост, уровень активности, цель, наличие заболеваний и аллергий) с последующим шифрованием данных с помощью `cryptography.fernet`.

- **Генерация плана питания и рецептов:**  
  Использование OpenAI API и LangChain для создания персонализированного плана питания, рецептов блюд с подробными инструкциями и визуальными образами (генерация изображений через DALL·E API).

- **Консультации по нутрициологии:**  
  Предоставление научно обоснованных рекомендаций с учетом индивидуальных данных пользователя.

- **Напоминания:**  
  Автоматические уведомления (с использованием Apscheduler) о необходимости пить воду для поддержания водного баланса.

## Технологии

- **Python**  
- **python-telegram-bot** – для работы с Telegram API  
- **SQLite** – для хранения данных пользователей  
- **Apscheduler** – для планирования задач и отправки уведомлений  
- **LangChain + OpenAI API** – для генерации текстового контента  
- **DALL·E API** – для генерации изображений блюд  
- **cryptography.fernet** – для шифрования и защиты данных

## Структура проекта

- `main.py` – точка входа в приложение, инициализация бота, регистрация обработчиков и запуск уведомлений.  
- `bot.py` – реализация логики бота, обработка команд и сообщений, регистрация пользователей.  
- `db.py` – работа с базой данных, хранение и шифрование персональных данных.  
- `keyboards.py` – конфигурация inline- и reply-клавиатур для взаимодействия с пользователями.  
- `nutrition_agent.py` – модуль для генерации персонального плана питания.  
- `recipes.py` – модуль для генерации рецептов блюд.  
- `reminders.py` – модуль для настройки и отправки уведомлений.  
- `generate_images.py` – модуль для генерации изображений через DALL·E API.  
- `consult.py` – модуль для генерации консультаций по нутрициологии.

## Установка и запуск

1. **Клонирование репозитория:**

   ```bash
   git clone https://github.com/elena/nutrition-bot
   cd nutrition-bot
   ```

2. **Установка зависимостей:**

   Установите необходимые библиотеки через pip:

   ```bash
   pip install -r requirements.txt
   ```

3. **Настройка переменных окружения:**

   Создайте файл `.env` в корне проекта и добавьте следующие переменные:
   
   ```
   BOT_TOKEN=your_telegram_bot_token
   OPENAI_API_KEY=your_openai_api_key
   ENCRYPTION_KEY=your_encryption_key
   ```

4. **Запуск бота:**

   Выполните команду:
   
   ```bash
   python main.py
   ```

## Скриншоты

В репозитории находятся скриншоты работы бота, демонстрирующие его функционал и интерфейс.

## Контакты

По вопросам сотрудничества и реализации данного проекта обращайтесь ко мне напрямую:  
**Елена Лоскутова**  
Телефон: +7 (917) 588-43-21  
Email: newlisa949@gmail.com  
Telegram: [@Elena_PromptLab](https://t.me/Elena_PromptLab)  
GitHub: [https://github.com/newLisa2024/MVP-NutriBot](https://github.com/newLisa2024/MVP-NutriBot)

