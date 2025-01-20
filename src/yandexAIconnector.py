
from typing import List, Dict, Optional
from yandex_cloud_ml_sdk import YCloudML
from dotenv import load_dotenv
import os

class DialogueManager:
    def __init__(self):
        load_dotenv()
        self.ya_folder = os.getenv('YA_FOLDER')
        self.ya_api_key = os.getenv('YA_API_KEY')
        self.temperature = float(os.getenv('TEMPERATURE', '0.6'))
        
        if not all([self.ya_folder, self.ya_api_key]):
            raise ValueError("Не найдены необходимые ключи окружения")
            
        self.sdk = YCloudML(
            folder_id=self.ya_folder,
            auth=self.ya_api_key,
        )
        self.model = self.sdk.models.completions("yandexgpt")
        self.model = self.model.configure(temperature=self.temperature)
    
    def get_reply(self, message_history: List[Dict[str, str]], system_line: Optional[str] = None) -> str:
        """
        Получает ответ от YandexGPT на историю сообщений.
        
        Args:
            message_history (List[Dict[str, str]]): История сообщений
            system_line (Optional[str]): Системный контекст
            
        Returns:
            str: Ответ модели
        """
        if not message_history or not isinstance(message_history, list):
            raise ValueError("История сообщений должна быть непустым списком")
            
        for message in message_history:
            if not isinstance(message, dict) or 'role' not in message or 'text' not in message:
                raise ValueError("Некорректный формат сообщения")
        
        messages = message_history.copy()
        if system_line:
            messages.append({'role': 'system', 'text': system_line})
        
        try:
            response = self.model.run(messages=messages)
            return response.alternatives[0].text
        except Exception as e:
            raise Exception(f"Ошибка YandexGPT: {str(e)}")