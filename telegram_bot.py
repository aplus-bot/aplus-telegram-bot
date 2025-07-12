import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Define the /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    response = f"Hello {user.username or 'User'}!\n\n"
    response += f"UserID: {user.id}\n"
    response += f"UserName: {user.username or 'N/A'}\n"
    if chat.type in ['group', 'supergroup']:
        response += f"GroupID: {chat.id}"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

# Main function to run the bot
def main():
    import os
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == '__main__':
    main()
