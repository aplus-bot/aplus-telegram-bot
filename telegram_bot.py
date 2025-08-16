import os
import re
import json
import logging
from datetime import datetime, timedelta
from telethon import TelegramClient
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio

# ===== Logging =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)

# ===== Telegram Bot API token =====
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ===== Telethon API credentials =====
API_ID = 23435657          # Replace with your api_id
API_HASH = "8d513f47e0492d0b2c4717e74a433364"  # Replace with your api_hash

# ===== Patterns =====
invoice_pattern = re.compile(r"🧾\s*វិក្កយបត្រ\s*(\d+)")
total_pattern = re.compile(r"💵\s*សរុប\s*:\s*\$([\d,.]+)\s*\|\s*R\.\s*([\d,]+)")

# ===== Data storage =====
DATA_FILE = "all_invoices.json"

# ===== Load/Save JSON =====
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== Record invoice =====
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

# ===== Telethon Client =====
tele_client = TelegramClient('userbot_session', API_ID, API_HASH)

async def get_group_id_by_name(group_name):
    await tele_client.start()
    async for dialog in tele_client.get_dialogs():
        if dialog.is_group and dialog.name == group_name:
            return dialog.id
    return None

# ===== Fetch all invoices (bot + users) =====
async def fetch_group_invoices(group_name, period='today'):
    group_id = await get_group_id_by_name(group_name)
    if not group_id:
        return f"Group '{group_name}' not found", []

    today = datetime.now().date()
    if period == "today":
        start_date = today
    elif period == "yesterday":
        start_date = today - timedelta(days=1)
    elif period == "week":
        start_date = today - timedelta(days=6)
    else:
        start_date = today

    invoices = []
    async for message in tele_client.iter_messages(group_id, reverse=True):
        if message.date.date() < start_date:
            break
        text = message.text or ""
        invoice_matches = invoice_pattern.findall(text)
        total_match = total_pattern.search(text)
        if invoice_matches and total_match:
            usd_amount = float(total_match.group(1).replace(",", ""))
            riel_amount = int(total_match.group(2).replace(",", ""))
            sender_id = message.sender_id or 0
            username = getattr(message.sender, "username", "Unknown") if message.sender else "Bot"
            for inv in invoice_matches:
                record_invoice(inv, usd_amount, riel_amount, sender_id, username)
                invoices.append({
                    "invoice_no": inv,
                    "usd": usd_amount,
                    "riel": riel_amount,
                    "user_id": sender_id,
                    "username": username
                })
    return None, invoices

# ===== Fetch bot-only invoices =====
async def fetch_bot_invoices(group_name, period='today', bot_username="Bot"):
    group_id = await get_group_id_by_name(group_name)
    if not group_id:
        return f"Group '{group_name}' not found", []

    today = datetime.now().date()
    if period == "today":
        start_date = today
    elif period == "yesterday":
        start_date = today - timedelta(days=1)
    elif period == "week":
        start_date = today - timedelta(days=6)
    else:
        start_date = today

    invoices = []
    async for message in tele_client.iter_messages(group_id, reverse=True):
        if message.date.date() < start_date:
            break
        # Bot messages usually have no sender or sender.username = bot username
        if not message.sender:
            text = message.text or ""
            invoice_matches = invoice_pattern.findall(text)
            total_match = total_pattern.search(text)
            if invoice_matches and total_match:
                usd_amount = float(total_match.group(1).replace(",", ""))
                riel_amount = int(total_match.group(2).replace(",", ""))
                for inv in invoice_matches:
                    record_invoice(inv, usd_amount, riel_amount, 0, bot_username)
                    invoices.append({
                        "invoice_no": inv,
                        "usd": usd_amount,
                        "riel": riel_amount,
                        "user_id": 0,
                        "username": bot_username
                    })
    return None, invoices

# ===== Bot commands =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    await update.message.reply_text(
        f"Hello {user.first_name}!\nUserID: {user.id}\nUserName: {user.username}\nGroupID: {chat.id if chat.type in ['group', 'supergroup'] else 'N/A'}"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n/start\n/help\n/about\n"
        "/dSum <group_name> [today|yesterday|week] - Sum all invoices\n"
        "/dSumBot <group_name> [today|yesterday|week] - Sum bot invoices only"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "About SystemBot:\n1) [Teacher Ngov Samnang](https://t.me/Aplus_SD)\n"
        "2) [Construction or Using](https://t.me/AplusSD_V5/194)\n"
        "3) [On Youtube](https://www.youtube.com/playlist?list=PLikM0v0bp6Cg8MC9hUnsZn9RU450YmFn0)"
    )

# ===== /dSum command (all invoices) =====
async def dsum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /dSum <group_name> [today|yesterday|week]")
        return
    group_name = context.args[0]
    period = context.args[1].lower() if len(context.args) > 1 else "today"

    error, invoices = await fetch_group_invoices(group_name, period)
    if error:
        await update.message.reply_text(error)
        return

    if not invoices:
        await update.message.reply_text(f"No invoices found for {period} in group '{group_name}'.")
        return

    usd_total = sum(inv['usd'] for inv in invoices)
    riel_total = sum(inv['riel'] for inv in invoices)

    lines = []
    for inv in invoices:
        lines.append(f"🧾 វិក្កយបត្រ  {inv['invoice_no']}")
        lines.append(f"💵 ${inv['usd']:,.2f} | R. {inv['riel']:,} | UserID: {inv['user_id']} | {inv['username']}")
    lines.append("_______________________")
    lines.append(f"💵 ${usd_total:,.2f} | R. {riel_total:,}")

    await update.message.reply_text("\n".join(lines))

# ===== /dSumBot command (bot-only invoices) =====
async def dsum_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /dSumBot <group_name> [today|yesterday|week]")
        return
    group_name = context.args[0]
    period = context.args[1].lower() if len(context.args) > 1 else "today"

    error, invoices = await fetch_bot_invoices(group_name, period, bot_username=update.bot.username)
    if error:
        await update.message.reply_text(error)
        return

    if not invoices:
        await update.message.reply_text(f"No bot invoices found for {period} in group '{group_name}'.")
        return

    usd_total = sum(inv['usd'] for inv in invoices)
    riel_total = sum(inv['riel'] for inv in invoices)

    lines = []
    for inv in invoices:
        lines.append(f"🧾 វិក្កយបត្រ  {inv['invoice_no']}")
        lines.append(f"💵 ${inv['usd']:,.2f} | R. {inv['riel']:,} | {inv['username']}")
    lines.append("_______________________")
    lines.append(f"💵 ${usd_total:,.2f} | R. {riel_total:,}")

    await update.message.reply_text("\n".join(lines))

# ===== Record user messages automatically =====
async def record_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    invoice_matches = invoice_pattern.findall(text)
    total_match = total_pattern.search(text)
    if invoice_matches and total_match:
        usd_amount = float(total_match.group(1).replace(",", ""))
        riel_amount = int(total_match.group(2).replace(",", ""))
        for inv in invoice_matches:
            record_invoice(inv, usd_amount, riel_amount,
                           update.effective_user.id,
                           update.effective_user.username or "Unknown")

# ===== Main =====
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("dSum", dsum_command))
    app.add_handler(CommandHandler("dSumBot", dsum_bot_command))

    # Record user messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, record_payment))

    app.run_polling()

if __name__ == "__main__":
    main()
