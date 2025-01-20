import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()

class Dialogue:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.character = None  # Хранит выбранного персонажа
        self.current_action = None  # Хранит текущую логику выбора (например, "выбор персонажа")

    async def send_message(self, context: ContextTypes.DEFAULT_TYPE, text: str, buttons: list = None, action: str = None):
        """Отправляет сообщение с кнопками и запоминает текущую логику."""
        reply_markup = None
        if buttons:
            keyboard = [[InlineKeyboardButton(btn, callback_data=btn)] for btn in buttons]
            reply_markup = InlineKeyboardMarkup(keyboard)

        self.current_action = action  # Сохраняем, что сейчас выбираем
        await context.bot.send_message(chat_id=self.chat_id, text=text, reply_markup=reply_markup)

# Словарь для хранения активных диалогов
dialogues = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in dialogues:
        dialogues[chat_id] = Dialogue(chat_id)
        await dialogues[chat_id].send_message(context, "Привет! Это бот для общения с персонажами!")

        # Вызываем выбор персонажа
        await choice_character(update, context)

async def choice_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    characters = ["Бэтмен", "Сократ"]
    await dialogues[chat_id].send_message(context, "Выберите персонажа:", buttons=characters, action="choose_character")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    if chat_id in dialogues:
        dialogue = dialogues[chat_id]
        selected_button = query.data  # Получаем текст кнопки

        if dialogue.current_action == "choose_character":
            # Логика для выбора персонажа
            dialogue.character = selected_button
            await query.edit_message_text(text=f"Вы выбрали персонажа: {selected_button}")

        else:
            # Если действие неизвестно
            await query.edit_message_text(text=f"Вы нажали на: {selected_button}")

def main():
    token = os.environ.get('BOT_TOKEN')
    if not token:
        raise ValueError("Токен бота не найден в переменных среды!")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling()

if __name__ == "__main__":
    main()