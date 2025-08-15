import logging
import os
import re
import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ===== Logging =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)

# ===== Regex patterns =====
invoice_pattern = re.compile(r"🧾\s*វិក្កយបត្រ\s*(\d+)")
total_pattern = re.compile(r"💵\s*សរុប\s*:\s*\$([\d,.]+)\s*\|\s*R\.\s*([\d,]+)")

# ===== Data storage =====
DATA_FILE_ALL = "daily_sum.json"       # All invoices
DATA_FILE_BOT = "daily_sum_bot.json"   # Bot-only invoices

def load_data(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== Record invoice =====
def record_invoice(invoice_no: str, usd: float, riel: int, bot_only=False):
    today_str = datetime.now().strftime("%Y-%m-%d")
    filename = DATA_FILE_BOT if bot_only else DATA_FILE_ALL
    data = load_data(filename)
    if today_str not in data:
        data[today_str] = []
    data[today_str].append({
        "invoice_no": invoice_no,
        "usd": usd,
        "riel": riel
    })
    save_data(filename, data)
    logging.info(f"{'Bot' if bot_only else 'User'} invoice #{invoice_no}: ${usd} | R. {riel}")

# ===== Send invoice (bot) =====
async def send_invoice(update: Update, msg_text: str):
    # Send message
    await update.message.reply_text(msg_text)

    # Parse invoice(s)
    invoice_matches = re.findall(invoice_pattern, msg_text)
    total_match = re.search(total_pattern, msg_text)

    if invoice_matches and total_match:
        usd_amount = float(total_match.group(1).replace(",", ""))
        riel_amount = int(total_match.group(2).replace(",", ""))
        for invoice_no in invoice_matches:
            record_invoice(invoice_no, usd_amount, riel_amount, bot_only=True)  # record bot invoice

# ===== Record user messages automatically =====
async def record_payment(update: Update, context):
    if not update.message or not update.message.text:
        return
    text = update.message.text
    invoice_matches = re.findall(invoice_pattern, text)
    total_match = re.search(total_pattern, text)
    if invoice_matches and total_match:
        usd_amount = float(total_match.group(1).replace(",", ""))
        riel_amount = int(total_match.group(2).replace(",", ""))
        for invoice_no in invoice_matches:
            record_invoice(invoice_no, usd_amount, riel_amount, bot_only=False)

# ===== Commands =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    await update.message.reply_text(
        f"Hello {user.first_name}!\nUserID: {user.id}\nUserName: {user.username}\nGroupID: {chat.id if chat.type in ['group', 'supergroup'] else 'N/A'}"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n/start\n/help\n/about\n/dSum [today|yesterday|week]\n/dSumBot [today|yesterday|week]"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "About SystemBot:\n1) [Teacher Ngov Samnang](https://t.me/Aplus_SD)\n"
        "2) [Construction or Using](https://t.me/AplusSD_V5/194)\n"
        "3) [On Youtube](https://www.youtube.com/playlist?list=PLikM0v0bp6Cg8MC9hUnsZn9RU450YmFn0)"
    )

# ===== /dSum (all invoices) =====
async def dsum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await sum_invoices(update, context, bot_only=False)

# ===== /dSumBot (bot-only invoices) =====
async def dsum_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await sum_invoices(update, context, bot_only=True)

# ===== Helper to sum invoices =====
async def sum_invoices(update, context, bot_only=False):
    filename = DATA_FILE_BOT if bot_only else DATA_FILE_ALL
    data = load_data(filename)
    today = datetime.now().date()
    period = context.args[0].lower() if context.args else "today"

    if period == "today":
        keys = [today.strftime("%Y-%m-%d")]
    elif period == "yesterday":
        keys = [(today - timedelta(days=1)).strftime("%Y-%m-%d")]
    elif period == "week":
        keys = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    else:
        await update.message.reply_text("Invalid argument. Use: today, yesterday, week")
        return

    invoices = []
    usd_total = 0.0
    riel_total = 0

    for key in keys:
        if key in data:
            for entry in data[key]:
                invoices.append(entry)
                usd_total += entry.get("usd", 0.0)
                riel_total += entry.get("riel", 0)

    if not invoices:
        await update.message.reply_text(f"No invoices found for {period}.")
        return

    # Build reply
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

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("dSum", dsum_command))
    app.add_handler(CommandHandler("dSumBot", dsum_bot_command))

    # Record user messages automatically
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, record_payment))

    app.run_polling()

if __name__ == "__main__":
    main()
