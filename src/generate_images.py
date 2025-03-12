import os
import requests
import datetime
import logging

logger = logging.getLogger(__name__)

# Получаем API-ключ из переменной окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def generate_image(prompt: str) -> str:
    """
    Отправляет запрос к DALL·E для генерации изображения на основе текстового описания.

    :param prompt: Текстовое описание изображения.
    :return: URL сгенерированного изображения или None, если произошла ошибка.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    data = {
        "model": "dall-e-3",  # Используем DALL·E 3
        "prompt": prompt,
        "n": 1,  # Количество изображений
        "size": "1024x1024"  # Размер изображения
    }
    response = requests.post("https://api.openai.com/v1/images/generations", headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result['data'][0]['url']
    else:
        logger.error("Ошибка при генерации изображения: %s", response.text)
        return None


def generate_recipe_image(recipe_prompt: str) -> str:
    """
    Генерирует изображение для рецепта, скачивает его и сохраняет в папку 'images'.
    Принимает визуально ориентированный промпт и возвращает путь к сохранённому файлу или None в случае ошибки.

    :param recipe_prompt: Текстовое описание для генерации изображения.
    :return: Путь к сохранённому файлу или None.
    """
    image_url = generate_image(recipe_prompt)
    if not image_url:
        return None

    try:
        image_response = requests.get(image_url)
        image_response.raise_for_status()
    except Exception as e:
        logger.error("Ошибка при скачивании изображения: %s", e, exc_info=True)
        return None

    image_dir = "images"
    os.makedirs(image_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recipe_{timestamp}.png"
    file_path = os.path.join(image_dir, filename)

    with open(file_path, "wb") as f:
        f.write(image_response.content)

    return file_path


if __name__ == "__main__":
    prompt = "Фотография аппетитного блюда 'Омлет с грибами и сыром', студийное освещение, высокое качество, яркие цвета"
    saved_image_path = generate_recipe_image(prompt)
    if saved_image_path:
        print(f"Изображение сохранено: {saved_image_path}")
    else:
        print("Не удалось сгенерировать или сохранить изображение.")



