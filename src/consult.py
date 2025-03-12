# consult.py
import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

load_dotenv()


def get_consultation(question: str, user_data: dict = None) -> str:
    """
    Генерирует ответ на вопрос пользователя с учетом данных его профиля (если они предоставлены).
    """
    try:
        if user_data:
            # Формируем персонализированный промпт
            system_prompt = (
                "Ты - диетолог-нутрициолог с 15-летним стажем. "
                "У пользователя, зарегистрированного с данными: возраст {age} лет, вес {weight} кг, рост {height} см, "
                "заболевания: {diseases}, аллергии: {allergies} и цель: {goal}, "
                "ответь на следующий вопрос: {question} "
                "Дай подробный и научно обоснованный ответ, учитывая индивидуальные особенности пользователя."
            )
            age = user_data.get("age", "неизвестно")
            weight = user_data.get("weight", "неизвестно")
            # Если рост не задан (регистрация может его не собирать), задаём значение по умолчанию:
            height = user_data.get("height", "неизвестно")
            diseases = user_data.get("diseases", "нет")
            allergies = user_data.get("allergies", "нет")
            goal = user_data.get("goal", "нет данных")
            formatted_prompt = system_prompt.format(
                age=age,
                weight=weight,
                height=height,
                diseases=diseases,
                allergies=allergies,
                goal=goal,
                question=question
            )
        else:
            # Если данные отсутствуют, используем общий промпт
            formatted_prompt = (
                "Ты - опытный диетолог-нутрициолог с 15-летним стажем. "
                "Ответь на следующий вопрос: {question} "
                "Дай подробный и научно обоснованный ответ."
            ).format(question=question)

        chain = (
                ChatPromptTemplate.from_template(formatted_prompt)
                | ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=700,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
                | StrOutputParser()
        )
        result = chain.invoke({})
        logger.info(f"Успешно сгенерирован ответ длиной {len(result)} символов")
        return result

    except Exception as e:
        logger.error(f"Ошибка при генерации ответа: {str(e)}", exc_info=True)
        return (
            "⚠️ Извините, не удалось обработать запрос. "
            "Попробуйте задать вопрос еще раз или обратитесь позже."
        )


