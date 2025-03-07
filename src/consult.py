# consult.py
import os
import logging
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Загрузка переменных окружения
load_dotenv()


# Инициализация цепочки обработки запросов
def create_consultation_chain():
    """Создаёт и возвращает цепочку для консультаций"""
    try:
        # Системный промпт с персонажем нутрициолога
        system_prompt = (
            "Ты - опытный нутрициолог с 10-летним стажем. "
            "Давай подробные, научно обоснованные ответы на русском языке. "
            "Учитывай возраст, вес и заболевания пользователя из его профиля. "
            "Если вопрос не связан с питанием, вежливо предложи задать другой вопрос."
        )

        # Создаем цепочку обработки
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{question}")
        ])

        return (
                prompt
                | ChatOpenAI(
            model_name="gpt-4o",
            temperature=0.7,
            max_tokens=500,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
                | StrOutputParser()
        )

    except Exception as e:
        logger.error(f"Ошибка инициализации цепочки: {str(e)}")
        raise


# Глобальная инициализация цепочки
consult_chain = create_consultation_chain()


def get_consultation(question: str) -> str:
    """Генерирует ответ на вопрос пользователя"""
    try:
        logger.info(f"Обработка вопроса: {question[:50]}...")  # Логируем начало обработки

        result = consult_chain.invoke({"question": question})

        logger.info(f"Успешно сгенерирован ответ длиной {len(result)} символов")
        return result

    except Exception as e:
        logger.error(f"Ошибка при генерации ответа: {str(e)}", exc_info=True)
        return (
            "⚠️ Извините, не удалось обработать запрос. "
            "Попробуйте задать вопрос еще раз или обратитесь позже."
        )


