from typing import List, Dict, Optional
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

def get_reply(message_history: List[Dict[str, str]], system_line: Optional[str] = None) -> str:
    """
    Получает ответ от YandexGPT на историю сообщений.
    
    Args:
        message_history (List[Dict[str, str]]): История сообщений, где каждое сообщение представляет собой словарь с ключами 'role' и 'text'
        system_line (Optional[str]): Контекст от системы
        
    Returns:
        str: Текст ответа модели
        
    Raises:
        ValueError: Если история сообщений пуста или не соответствует формату
    """
    if not message_history or not isinstance(message_history, list):
        raise ValueError("История сообщений должна быть непустым списком словарей")
        
    for message in message_history:
        if not isinstance(message, dict) or 'role' not in message or 'text' not in message:
            raise ValueError("Каждое сообщение должно быть словарем с ключами 'role' и 'text'")
    
    if system_line:
        message_history.append({'role': 'system', 'text': system_line})
    
    try:
        response = model.run(messages=message_history)
        return response.alternatives[0].text
    except Exception as e:
        raise Exception(f"Ошибка получения ответа от YandexGPT: {str(e)}")

if __name__ == '__main__':
    history = [
        {'role': 'user', 'text': 'Привет, как тебя зовут?'},
        {'role': 'assistant', 'text': 'Я YandexGPT, приятно познакомиться!'},
        {'role': 'user', 'text': 'Расскажи мне о том что такое электрический ток'}
    ]
    system_context = 'Твой ответ должен быть неформальным, отвечай как двачер, битард, тролль'
    try:
        reply = get_reply(history, system_line=system_context)
        print(reply)
    except Exception as e:
        print(f"Error: {e}")
