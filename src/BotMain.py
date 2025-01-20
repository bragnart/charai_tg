import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from YandexAIConnector import DialogueManager
from CharLogic import Character

load_dotenv()

# Конфигурации персонажей
CHARACTERS = {
    "Бэтмен": {
        "name": "Batman",
        "description": "Защитник Готэма",
        "start_line": "Ты - Бэтмен, защитник Готэма...",
        "snippets": [
            {'role': 'user', 'text': 'Кто ты такой?'},
            {'role': 'assistant', 'text': 'Я тот, кто нужен этому городу. Я - Бэтмен.'}
        ],
        "greetings": "Я - Бэтмен. Говори быстро, у преступности нет выходных."
    },
    "Дракула": {
        "name": "Count Dracula",
        "description": "Древний вампир",
        "start_line": "Ты - граф Дракула...",
        "snippets": [
            {'role': 'user', 'text': 'Добрый вечер, граф'},
            {'role': 'assistant', 'text': 'Ах, добрый вечер... Какая восхитительная ночь.'}
        ],
        "greetings": "Добро пожаловать в мой замок..."
    }
}

class Dialogue:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.character = None  # Объект Character
        self.current_action = None
        self.dialogue_manager = DialogueManager()  # Создаем менеджер диалогов

    def create_character(self, character_name: str):
        """Создает объект персонажа по его имени"""
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
    if chat_id not in dialogues:
        dialogues[chat_id] = Dialogue(chat_id)
        await dialogues[chat_id].send_message(context, "Привет! Это бот для общения с персонажами!")
        await choice_character(update, context)

async def choice_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    characters = list(CHARACTERS.keys())
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

def main():
    token = os.environ.get('BOT_TOKEN')
    if not token:
        raise ValueError("Токен бота не найден в переменных среды!")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()