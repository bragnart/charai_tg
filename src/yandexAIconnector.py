from typing import Optional, List, Dict, Union
from yandex_cloud_ml_sdk import YCloudML
from dotenv import load_dotenv
import os

load_dotenv()
YA_FOLDER = os.getenv('YA_FOLDER')
YA_API_KEY = os.getenv('YA_API_KEY')
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.6'))  # Дефолтная температура, если не установлена

# Проверяем наличие переменных среды
if not all([YA_FOLDER, YA_API_KEY]):
    raise ValueError("Не найдены необходимые ключи")

sdk = YCloudML(
    folder_id=YA_FOLDER,
    auth=YA_API_KEY,
)
model = sdk.models.completions("yandexgpt")
model = model.configure(temperature=TEMPERATURE)

def get_answer(question: str, system_line: Optional[str] = None) -> str:
    """
    Получает ответ от YandexGPT.
    
    Args:
        question (str): Вопрос юзера
        system_line (Optional[str]): Контекст от системы 
        
    Returns:
        str: Текст ответа модели
        
    Raises:
        ValueError: Если вопрос пуст
    """
    if not question or not isinstance(question, str):
        raise ValueError("Вопрос должен быть не пустой строкой")
        
    try:
        messages = [{'role': 'user', 'text': question}]
        if system_line:
            messages.append({'role': 'system', 'text': system_line})
            
        response = model.run(messages=messages)
        return response.alternatives[0].text
    except Exception as e:
        raise Exception(f"Ошибка получения ответа от YandexGPT: {str(e)}")

if __name__ == '__main__':
    question = 'Какой самый длинный остров в мире?'
    try:
        answer = get_answer(question)
        print(answer)
    except Exception as e:
        print(f"Error: {e}")