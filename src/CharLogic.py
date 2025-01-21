from typing import List, Dict
import json
from YandexAIConnector import DialogueManager
from prompts import *

class Character:
    def __init__(self, user: str, name: str, description: str, 
                 start_line: str, snippets: List[Dict[str, str]], 
                 greetings: str, dialogue_manager: DialogueManager):
        """
        Инициализация персонажа для диалога.
        
        Args:
            user (str): Имя пользователя
            name (str): Имя персонажа
            description (str): Описание персонажа
            start_line (str): Начальный системный промпт
            snippets (List[Dict[str, str]]): Примеры диалогов для обучения
            greetings (str): Приветственная фраза
            dialogue_manager (DialogueManager): Менеджер диалогов для работы с API
        """
        self.user = user
        self.name = name
        self.description = description
        self.start_line = start_line
        self.snippets = snippets
        self.greetings = greetings
        self.dialogue_manager = dialogue_manager
        
        self.interactions = []
        self.init_dialogue()
        
    def init_dialogue(self):
        """Инициализация начального состояния диалога"""
        self.interactions = [
            {'role': 'system', 'text': self.start_line},
            *self.snippets,
            {'role': 'assistant', 'text': self.greetings}
        ]
    
    def add_user_message(self, message: str) -> str:
        """
        Добавление сообщения пользователя и получение ответа.
        
        Args:
            message (str): Сообщение пользователя
            
        Returns:
            str: Ответ персонажа
        """
        if not message.strip():
            raise ValueError("Сообщение не может быть пустым")
            
        # Добавляем сообщение пользователя
        self.interactions.append({
            'role': 'user',
            'text': message
        })
        
        # Получаем ответ от модели
        response = self.dialogue_manager.get_reply(
            message_history=self.interactions
        )
        
        # Добавляем ответ в историю
        self.interactions.append({
            'role': 'assistant',
            'text': response
        })
        
        return response
    
    def read_interactions(self) -> List[str]:
        """
        Получение истории диалога в читаемом формате.
        
        Returns:
            List[str]: Список строк диалога
        """
        dialogue = []
        for msg in self.interactions:
            prefix = {
                'user': self.user,
                'system': 'Система',
                'assistant': self.name
            }.get(msg['role'], msg['role'])
            
            line = f"{prefix}: {msg['text']}"
            dialogue.append(line)
        return dialogue
    

    def let_fight(self, enemy, instructions):
        """Устраивает битву персонажа с указанным врагом"""
        if self.name != "":
            # Получаем инструкции и отправляем их в менеджер диалогов
            msg = f"Начать бой с {enemy}.\nУказания для персонажа и какой инвентарь дан для боя: {instructions}"
            self.interactions.append({'role':'user','text':msg})
            fight_msg = self.dialogue_manager.get_reply(self.interactions,FIGHT_PROMPT)
            self.interactions.append({'role':'system','text':fight_msg})
            return fight_msg


    def save_dialogue(self, filename: str):
        """Сохранение диалога в JSON файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.interactions, f, ensure_ascii=False, indent=2)
    
    def load_dialogue(self, filename: str):
        """Загрузка диалога из JSON файла"""
        with open(filename, 'r', encoding='utf-8') as f:
            self.interactions = json.load(f)