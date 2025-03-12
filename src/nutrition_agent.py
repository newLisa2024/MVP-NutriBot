import logging
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()

# Настройка логгера
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
    """
    Вычисляет базальный метаболизм (BMR) по формуле Mifflin-St Jeor.
    Для мужчин: BMR = 10*weight + 6.25*height - 5*age + 5
    Для женщин: BMR = 10*weight + 6.25*height - 5*age - 161
    """
    if gender.lower() == 'male':
        return 10 * weight + 6.25 * height - 5 * age + 5
    else:
        return 10 * weight + 6.25 * height - 5 * age - 161

def generate_nutrition_plan(user_data: dict) -> str:
    """
    Генерирует персональный план питания на основе данных пользователя.
    Ожидается, что в user_data присутствуют следующие ключи:
      - 'age': возраст (в годах)
      - 'weight': вес (в кг)
      - 'height': рост (в см)
      - 'gender': пол ('male' или 'female')
      - 'goal': цель (например, "похудение", "набор массы" или "поддержание здоровья")
      - 'allergies': информация об аллергиях
      - 'diseases': информация о хронических заболеваниях
    Если какие-либо данные отсутствуют, используются значения по умолчанию.
    """
    try:
        # Извлечение данных с установкой дефолтных значений
        weight = float(user_data.get('weight', 70))
        height = float(user_data.get('height', 170))
        age = int(user_data.get('age', 30))
        gender = user_data.get('gender', 'male')
        goal = user_data.get('goal', 'поддержание здоровья')
        allergies = user_data.get('allergies', 'нет')
        diseases = user_data.get('diseases', 'нет')

        # Расчет BMR и суточной калорийности (примерный коэффициент активности = 1.2)
        bmr = calculate_bmr(weight, height, age, gender)
        daily_calories = bmr * 1.2

        # Формирование промпта для генерации плана питания
        prompt_text = (
            "Ты опытный диетолог с многолетним стажем. "
            "На основе следующих данных пользователя сформируй персональный план питания:\n"
            "Возраст: {age} лет\n"
            "Вес: {weight} кг\n"
            "Рост: {height} см\n"
            "Пол: {gender}\n"
            "Цель: {goal}\n"
            "Хронические заболевания: {diseases}\n"
            "Аллергии: {allergies}\n"
            "Базальный метаболизм (BMR): {bmr:.0f} калорий\n"
            "Рекомендуемая суточная калорийность: {daily_calories:.0f} калорий\n\n"
            "Составь подробный план питания, включая примерное меню на день, рекомендации по распределению макроэлементов и советы по питанию."
        )
        prompt_filled = prompt_text.format(
            age=age,
            weight=weight,
            height=height,
            gender=gender,
            goal=goal,
            diseases=diseases,
            allergies=allergies,
            bmr=bmr,
            daily_calories=daily_calories
        )

        # Создание цепочки для генерации ответа через LLM с использованием LangChain
        chain = (
            ChatPromptTemplate.from_template(prompt_filled)
            | ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=1000,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
            | StrOutputParser()
        )
        result = chain.invoke({})
        return result

    except Exception as e:
        logger.error(f"Ошибка генерации плана питания: {e}", exc_info=True)
        return "Ошибка генерации плана питания. Попробуйте позже."

if __name__ == '__main__':
    # Пример использования функции с тестовыми данными пользователя
    sample_user_data = {
        'age': '30',
        'weight': '70',
        'height': '170',
        'gender': 'male',
        'goal': 'похудение',
        'allergies': 'нет',
        'diseases': 'нет'
    }
    plan = generate_nutrition_plan(sample_user_data)
    print(plan)

