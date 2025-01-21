import os
import asyncio
import json
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from YandexAIConnector import DialogueManager
from CharLogic import Character
from prompts import *

load_dotenv()
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'CharConfig.json')

class Dialogue:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.character = None  # Объект Character
        self.current_action = None
        self.dialogue_manager = DialogueManager()  # Создаем менеджер диалогов

    def create_character(self, character_name: str):
        """Создает объект персонажа по его имени"""
        try:
            CHARACTERS = json.load(open(config_path, "r", encoding='utf-8'))  # Загружаем конфигурацию персонажей
            if character_name in CHARACTERS:
                config = CHARACTERS[character_name]
                self.character = Character(
                    user=str(self.chat_id),
                    name=config["name"],
                    description=config["description"],
                    start_line=config["start_line"],
                    snippets=config["snippets"],
                    greetings=config["greetings"],
                    dialogue_manager=self.dialogue_manager
                )
                return True
            else:
                print(f"{self.chat_id} попытался выбрать персонажа {character_name} а его нет")
                return False
        except Exception as e:
            print(f"Произошла ошибка при создании персонажа: {str(e)}")
            return False

    async def send_message(self, context: ContextTypes.DEFAULT_TYPE, text: str, buttons: list = None, action: str = None):
        """Отправляет сообщение с кнопками и запоминает текущую логику"""
        reply_markup = None
        if buttons:
            keyboard = [[InlineKeyboardButton(btn, callback_data=btn)] for btn in buttons]
            reply_markup = InlineKeyboardMarkup(keyboard)

        self.current_action = action
        await context.bot.send_message(chat_id=self.chat_id, text=text, reply_markup=reply_markup)

# Словарь для хранения активных диалогов
dialogues = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Если диалог уже существует, сбрасываем его
    if chat_id in dialogues:
        del dialogues[chat_id]

    # Создаем новый диалог
    dialogues[chat_id] = Dialogue(chat_id)
    await dialogues[chat_id].send_message(context, "Привет! Это бот для общения с персонажами!")
    await choice_character(update, context)
    
async def choice_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Убедимся, что диалог существует (на случай, если эта функция вызвана не через /start)
    if chat_id not in dialogues:
        dialogues[chat_id] = Dialogue(chat_id)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            characters_config = json.load(f)
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Ошибка при загрузке конфигурации персонажей."
        )
        print(f"Ошибка {e}")
        return

    characters = list(characters_config.keys())
    await dialogues[chat_id].send_message(
        context,
        "Выберите персонажа:",
        buttons=characters,
        action="choose_character"
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    if chat_id in dialogues:
        dialogue = dialogues[chat_id]
        selected_button = query.data

        if dialogue.current_action == "choose_character":
            if dialogue.create_character(selected_button):
                await query.edit_message_text(
                    text=f"Вы начали диалог с персонажем: {selected_button}\n\n" +
                         dialogue.character.greetings
                )
            else:
                await query.edit_message_text(text="Произошла ошибка при выборе персонажа")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений от пользователя"""
    chat_id = update.effective_chat.id
    if chat_id in dialogues and dialogues[chat_id].character:
        dialogue = dialogues[chat_id]
        user_message = update.message.text
        
        try:
            # Получаем ответ от персонажа
            response = dialogue.character.add_user_message(user_message)
            await context.bot.send_message(chat_id=chat_id, text=response)
        except Exception as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Произошла ошибка при обработке сообщения. Попробуйте еще раз."
            )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Пожалуйста, сначала выберите персонажа с помощью команды /start"
        )


async def conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /conversation для диалога между персонажами"""
    chat_id = update.effective_chat.id
    
    # Проверяем аргументы
    if not context.args or len(context.args) < 2 or len(context.args) > 4:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Пожалуйста, укажите от 2 до 4 персонажей через пробел.\n"
                 "Например: /conversation Бэтмен 'Шерлок Холмс' Дракула"
        )
        return

    # Загружаем конфигурации персонажей
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            characters_config = json.load(f)
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text="Ошибка при загрузке конфигурации персонажей."
        )
        return

    # Проверяем существование всех персонажей
    characters = context.args
    for char in characters:
        if char not in characters_config:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Персонаж '{char}' не найден. Доступные персонажи: {', '.join(characters_config.keys())}"
            )
            return

    # Сбрасываем текущий диалог
    if chat_id in dialogues:
        dialogues[chat_id].character = None

    # Создаем экземпляры персонажей для диалога
    dialogue_manager = DialogueManager()
    char_instances = {}
    
    for char_name in characters:
        config = characters_config[char_name]
        char_instances[char_name] = Character(
            user="System",
            name=config["name"],
            description=config["description"],
            start_line=config["start_line"],
            snippets=config["snippets"],
            greetings=config["greetings"],
            dialogue_manager=dialogue_manager
        )

    # Начинаем диалог
    await context.bot.send_message(
        chat_id=chat_id,
        text="Начинаем диалог между персонажами..."
    )

    # Два круга реплик
    for round in range(2):
        for i, current_char in enumerate(characters):
            # Формируем промпт для текущего персонажа
            if round == 0 and i == 0:
                prompt = "Начни диалог с представления себя и обращения к собеседникам"
            else:
                # Получаем предыдущего персонажа
                prev_char = characters[(i - 1) % len(characters)]
                prompt = f"Ответь на реплику персонажа {prev_char}"

            try:
                response = char_instances[current_char].add_user_message(prompt)
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"{current_char}: {response}"
                )
                await asyncio.sleep(2)  # Пауза между репликами
            except Exception as e:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"Ошибка при получении ответа от {current_char}."
                )
                return

    await context.bot.send_message(
        chat_id=chat_id,
        text="Диалог завершен. Используйте /start чтобы начать новый диалог с персонажем."
    )

async def to_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /to_all для отправки сообщения всем пользователям"""
    if 'BOT_TOKEN' not in os.environ:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="API ключ бота не найден!")
        return

    if not context.args:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Пожалуйста, укажите текст для отправки.")
        return

    message = ' '.join(context.args)

    for chat_id in dialogues.keys():
        await context.bot.send_message(chat_id=chat_id, text=message)

async def shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /shutdown для завершения работы бота"""
    if 'BOT_TOKEN' not in os.environ:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="API ключ бота не найден!")
        return

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Завершение работы бота...")
    await context.bot.application.stop()
    await context.bot.stop()

def main():
    token = os.environ.get('BOT_TOKEN')
    if not token:
        raise ValueError("Токен бота не найден в переменных среды!")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("conversation", conversation))  # Новый обработчик
    application.add_handler(CommandHandler("to_all", to_all))  # Новый обработчик
    application.add_handler(CommandHandler("shutdown", shutdown))  # Новый обработчик
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()