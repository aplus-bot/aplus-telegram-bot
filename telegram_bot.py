import logging
import os
import re
import json
from datetime import datetime, timedelta
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ===== Logging =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)

# ===== Regex patterns =====
invoice_pattern = re.compile(r"🧾\s*វិក្កយបត្រ\s*(\d+)")
usd_pattern = re.compile(r"💵\s*សរុប\s*:\s*\$([\d,.]+)")
riel_pattern = re.compile(r"\|\s*R\.\s*([\d,]+)")

# ===== Data file =====
DATA_FILE = "daily_sum.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== Record each invoice =====
async def record_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Include all messages, even from the bot
    if not update.message or not update.message.text:
        return

    text = update.message.text
    invoice_match = invoice_pattern.search(text)
    usd_match = usd_pattern.search(text)
    riel_match = riel_pattern.search(text)

    if invoice_match and (usd_match or riel_match):
        today_str = datetime.now().strftime("%Y-%m-%d")
        data = load_data()

        if today_str not in data:
            data[today_str] = []

        invoice_no = invoice_match.group(1)
        usd_amount = float(usd_match.group(1).replace(",", "")) if usd_match else 0.0
        riel_amount = int(riel_match.group(1).replace(",", "")) if riel_match else 0

        data[today_str].append({
            "invoice_no": invoice_no,
            "usd": usd_amount,
            "riel": riel_amount
        })

        save_data(data)
        logging.info(f"Recorded invoice #{invoice_no} for {today_str}: ${usd_amount} | R. {riel_amount}")

# ===== Commands =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    await update.message.reply_text(
        f"Hello {user.first_name}!\nUserID: {user.id}\nUserName: {user.username}\nGroupID: {chat.id if chat.type in ['group', 'supergroup'] else 'N/A'}"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n/start\n/help\n/about\n/dSum [today|yesterday|week]"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "About SystemBot:\n1) [Teacher Ngov Samnang](https://t.me/Aplus_SD)\n"
        "2) [Construction or Using](https://t.me/AplusSD_V5/194)\n"
        "3) [On Youtube](https://www.youtube.com/playlist?list=PLikM0v0bp6Cg8MC9hUnsZn9RU450YmFn0)"
    )

# ===== /dSum with two-line invoices + separator + grand total =====
async def dsum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
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

    # Build reply: each invoice two lines
    lines = []
    for inv in invoices:
        lines.append(f"🧾 វិក្កយបត្រ  {inv['invoice_no']}")
        lines.append(f"💵 ${inv['usd']:,.2f} | R. {inv['riel']:,}")

    # Separator line
    lines.append("_______________________")

    # Grand total after separator
    lines.append(f"💵 ${usd_total:,.2f} | R. {riel_total:,}")

    reply = "\n".join(lines)
    await update.message.reply_text(reply)

# ===== Main =====
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("dSum", dsum_command))

    # Message handler to record all payments (including bot messages)
    app.add_handler(MessageHandler(filters.TEXT, record_payment))

    app.run_polling()

if __name__ == "__main__":
    main()
