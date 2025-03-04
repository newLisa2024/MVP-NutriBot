import os
from dotenv import load_dotenv
import openai

# Импортируем ChatOpenAI из пакета langchain-openai
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)

# Загружаем переменные окружения
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Создаем шаблон для чата:
# - SystemMessage задаёт роль ассистента (эксперта по питанию)
# - HumanMessage принимает вопрос пользователя
chat_prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(
        "Ты – эксперт по питанию и здоровому образу жизни. Отвечай на вопросы пользователя подробно и понятно, на русском языке."
    ),
    HumanMessagePromptTemplate.from_template("{question}")
])

# Создаем цепочку, которая вызывает модель OpenAI через ChatOpenAI
chain = LLMChain(
    llm=ChatOpenAI(temperature=0.7, max_tokens=200),
    prompt=chat_prompt
)


def get_consultation(question: str) -> str:
    """
    Получает ответ модели по заданному вопросу.

    :param question: Текст вопроса пользователя.
    :return: Ответ модели как строка.
    """
    return chain.run({"question": question})


