import logging
import os
import re
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ===== Logging =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)

# ===== JSON file for daily invoices =====
DATA_FILE = "daily_invoices.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def record_invoice(invoice_no, usd, riel, user_id, username):
    today_str = datetime.now().strftime("%Y-%m-%d")
    data = load_data()
    if today_str not in data:
        data[today_str] = []
    data[today_str].append({
        "invoice_no": invoice_no,
        "usd": usd,
        "riel": riel,
        "user_id": user_id,
        "username": username
    })
    save_data(data)
    logging.info(f"Invoice #{invoice_no} recorded: ${usd} | R. {riel} by {username}")

# ===== Regex patterns =====
invoice_pattern = re.compile(r"🧾\s*វិក្កយបត្រ\s*(\d+)")
total_pattern = re.compile(r"💵\s*សរុប\s*:\s*\$([\d,.]+)\s*\|\s*R\.\s*([\d,]+)")

# ===== /start command =====
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

# ===== /help command =====
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = (
        "Available commands:\n"
        "/start - Show user info\n"
        "/help - List available commands\n"
        "/about - About this bot\n"
        "/Sum - Sum all invoices today (including bot messages)"
    )
    await update.message.reply_text(response)

# ===== /about command =====
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = (
        "About SystemBot:\n"
        "1) [Teacher Ngov Samnang](https://t.me/Aplus_SD)\n"
        "2) [Construction or Using](https://t.me/AplusSD_V5/194)\n"
        "3) [On Youtube](https://www.youtube.com/playlist?list=PLikM0v0bp6Cg8MC9hUnsZn9RU450YmFn0)"
    )
    await update.message.reply_text(response)

# ===== Record user messages =====
async def record_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    invoice_matches = invoice_pattern.findall(text)
    total_match = total_pattern.search(text)
    if invoice_matches and total_match:
        usd_amount = float(total_match.group(1).replace(",", ""))
        riel_amount = int(total_match.group(2).replace(",", ""))
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        for inv in invoice_matches:
            record_invoice(inv, usd_amount, riel_amount, user_id, username)

# ===== Bot sends invoice and records it automatically =====
async def send_invoice(update: Update, msg_text: str):
    # Send the invoice
    sent_msg = await update.message.reply_text(msg_text)

    # Extract invoice numbers and totals
    invoice_matches = invoice_pattern.findall(msg_text)
    total_match = total_pattern.search(msg_text)
    if invoice_matches and total_match:
        usd_amount = float(total_match.group(1).replace(",", ""))
        riel_amount = int(total_match.group(2).replace(",", ""))
        for inv in invoice_matches:
            record_invoice(inv, usd_amount, riel_amount, user_id=0, username="Bot")

# ===== /Sum command =====
async def sum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today_str = datetime.now().strftime("%Y-%m-%d")
    data = load_data()
    invoices = data.get(today_str, [])

    if not invoices:
        await update.message.reply_text("No invoices recorded today.")
        return

    usd_total = sum(inv["usd"] for inv in invoices)
    riel_total = sum(inv["riel"] for inv in invoices)

    lines = []
    for inv in invoices:
        lines.append(f"🧾 វិក្កយបត្រ  {inv['invoice_no']}")
        lines.append(f"💵 ${inv['usd']:,.2f} | R. {inv['riel']:,}")
    lines.append("_______________________")
    lines.append(f"💵 ${usd_total:,.2f} | R. {riel_total:,}")

    await update.message.reply_text("\n".join(lines))

# ===== Main =====
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("Sum", sum_command))

    # Record all user messages automatically
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, record_user_message))

    app.run_polling()

if __name__ == "__main__":
    main()
