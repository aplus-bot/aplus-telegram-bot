import logging
import os
import platform  # Import platform module for system information
import time      # Import time module for uptime calculation
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Enable logging to a file
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    response = (
        f"Hello {user.first_name}!\n\n"
        f"UserID: {user.id}\n"
        f"UserName: {user.username}\n"
        f"GroupID: {chat.id if chat.type in ['group', 'supergroup'] else 'N/A'}"
    )
    await update.message.reply_text(response)
    logging.info(f"/start used by {user.username} ({user.id}) in chat {chat.id}")

# /help command handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = (
        "Available commands:\n"
        "/start - Show user info\n"
        "/help - List available commands\n"
        "/about - About this bot\n"  # Added newline for /system command
        "/system - Show system information"  # Added /system description
    )
    await update.message.reply_text(response)
    user = update.effective_user
    chat = update.effective_chat
    logging.info(f"/help used by {user.username} ({user.id}) in chat {chat.id}")

# /about command handler
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = (
        "About SystemBot:\n"
        "1) [Teacher Ngov Samnang](https://t.me/Aplus_SD)\n"
        "2) [Contruction or Using] (https://t.me/AplusSD_V5/194)\n"
        "3) [On Youtube](https://www.youtube.com/playlist?list=PLikM0v0bp6Cg8MC9hUnsZn9RU450YmFn0)"
    )
    await update.message.reply_text(response)
    user = update.effective_user
    chat = update.effective_chat
    logging.info(f"/about used by {user.username} ({user.id}) in chat {chat.id}")

# /system command handler - NEW COMMAND
async def system_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get OS name and hostname
    os_name = platform.system()
    hostname = platform.node()
    
    # Calculate formatted uptime
    uptime_seconds = time.monotonic()
    days, remainder = divmod(int(uptime_seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    
    # Create response
    response = (
        f"OS: {os_name}\n"
        f"Hostname: {hostname}\n"
        f"Uptime: {uptime_str}"
    )
    await update.message.reply_text(response)
    
    # Log command usage
    user = update.effective_user
    chat = update.effective_chat
    logging.info(f"/system used by {user.username} ({user.id}) in chat {chat.id}")

# Main function to run the bot
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("system", system_command))  # Added system command handler

    app.run_polling()

# Run the bot
if __name__ == "__main__":
    main()
