import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

def generate_recipe_with_openai(ingredients: str, user_context: dict) -> str:
    """Генерация рецепта с улучшенной обработкой ошибок"""
    try:
        # Debug-лог: выводим входные данные для отладки
        logger.debug(
            "generate_recipe_with_openai вызвана с данными:\n"
            f"ingredients={ingredients}, user_context={user_context}"
        )

        # Проверка на пустые ингредиенты
        if not ingredients.strip():
            return "❌ Пожалуйста, укажите ингредиенты"

        # Промпт с учётом целей пользователя
        prompt_text = (
            "Ты шеф-повар и диетолог. Создай рецепт используя: {ingredients}\n"
            "Учти:\n"
            "- Аллергии: {allergies}\n"
            "- Цель: {goal}\n"
            "Формат:\n"
            "1. 🍽️ Название блюда\n"
            "2. 📋 Ингредиенты\n"
            "3. 🧑🍳 Приготовление\n"
            "4. 🏷️ КБЖУ"
        )

        chain = (
            ChatPromptTemplate.from_template(prompt_text)
            | ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
            | StrOutputParser()
        )

        return chain.invoke({
            "ingredients": ingredients,
            "allergies": user_context.get("allergies", "нет"),
            "goal": user_context.get("goal", "нет данных")
        })

    except Exception as e:
        logger.error(f"Ошибка генерации: {str(e)}", exc_info=True)
        return "⚠️ Не удалось создать рецепт. Проверьте ингредиенты и попробуйте снова."
