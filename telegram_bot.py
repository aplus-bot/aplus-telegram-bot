import logging
import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)

# ------------------- In-memory storage -------------------
# Structure: {chat_id: {"USD": total_usd, "Riel": total_riel}}
group_totals = {}

# ------------------- Message Handler -------------------
async def collect_amounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Include all messages, even bot's own messages

    text = update.message.text
    # Regex to match amounts
    match = re.search(r'💵 សរុប : \$([\d,.]+)\s*\|\s*R\. ([\d,]+)', text)
    if match:
        usd = float(match.group(1).replace(',', ''))
        riel = int(match.group(2).replace(',', ''))

        chat_id = update.message.chat.id
        if chat_id not in group_totals:
            group_totals[chat_id] = {"USD": 0, "Riel": 0}

        group_totals[chat_id]["USD"] += usd
        group_totals[chat_id]["Riel"] += riel

# ------------------- /sum Command -------------------
async def sum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat.id
    totals = group_totals.get(chat_id, {"USD": 0, "Riel": 0})
    response = f"💵 Total USD: ${totals['USD']:,.2f}\n💵 Total Riel: R. {totals['Riel']:,}"
    await update.message.reply_text(response)

# ------------------- Main -------------------
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("sum", sum_command))

    # Listen to all text messages (excluding commands)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, collect_amounts))

    app.run_polling()

# ------------------- Start, Help, About -------------------
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = (
        "Available commands:\n"
        "/start - Show user info\n"
        "/help - List available commands\n"
        "/about - About this bot\n"
        "/sum - Sum all amounts in this group"
    )
    await update.message.reply_text(response)
    user = update.effective_user
    chat = update.effective_chat
    logging.info(f"/help used by {user.username} ({user.id}) in chat {chat.id}")

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

if __name__ == "__main__":
    main()
