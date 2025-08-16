import os
import logging
import re
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telethon import TelegramClient

# ===== Logging =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)

# ===== Telethon setup =====
api_id = 123456           # Replace with your api_id
api_hash = 'YOUR_API_HASH'  # Replace with your api_hash
session_name = 'bot_client'

GROUP_ID = -1001234567890  # Replace with your group ID

invoice_pattern = re.compile(r"🧾\s*វិក្កយបត្រ\s*(\d+)")
total_pattern = re.compile(r"💵\s*សរុប\s*:\s*\$([\d,.]+)\s*\|\s*R\.\s*([\d,]+)")

tele_client = TelegramClient(session_name, api_id, api_hash)

# ===== Fetch invoices sent today =====
async def fetch_invoices():
    usd_total = 0.0
    riel_total = 0
    invoice_lines = []

    today_str = datetime.now().strftime("%Y-%m-%d")

    async for message in tele_client.iter_messages(GROUP_ID, limit=1000):
        text = message.text or ""
        msg_date = message.date.strftime("%Y-%m-%d")
        if msg_date != today_str:
            continue  # skip messages not from today

        invoices = invoice_pattern.findall(text)
        total_match = total_pattern.search(text)
        if invoices and total_match:
            usd = float(total_match.group(1).replace(",", ""))
            riel = int(total_match.group(2).replace(",", ""))
            usd_total += usd
            riel_total += riel
            for inv_no in invoices:
                invoice_lines.append(f"🧾 វិក្កយបត្រ {inv_no}")
                invoice_lines.append(f"💵 ${usd:,.2f} | R. {riel:,}")

    if invoice_lines:
        invoice_lines.append("_______________________")
        invoice_lines.append(f"💵 ${usd_total:,.2f} | R. {riel_total:,}")

    return "\n".join(invoice_lines) if invoice_lines else "No invoices found today."

# ===== Telegram bot commands =====
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
    response = "Available commands:\n/start\n/help\n/about\n/sum"
    await update.message.reply_text(response)

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = (
        "About SystemBot:\n"
        "1) [Teacher Ngov Samnang](https://t.me/Aplus_SD)\n"
        "2) [Construction or Using](https://t.me/AplusSD_V5/194)\n"
        "3) [On Youtube](https://www.youtube.com/playlist?list=PLikM0v0bp6Cg8MC9hUnsZn9RU450YmFn0)"
    )
    await update.message.reply_text(response)

async def sum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    invoice_text = await fetch_invoices()
    await update.message.reply_text(invoice_text)

# ===== Run bot and Telethon client =====
async def main():
    # Start Telethon client
    await tele_client.start()
    print("Telethon client started")

    # Start Telegram bot
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("sum", sum_command))  # /sum command

    # Run bot polling
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
