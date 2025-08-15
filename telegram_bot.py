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

# ===== Record incoming messages =====
async def record_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    usd_match = usd_pattern.search(text)
    riel_match = riel_pattern.search(text)

    if usd_match or riel_match:
        today_str = datetime.now().strftime("%Y-%m-%d")
        data = load_data()

        if today_str not in data:
            data[today_str] = {"usd": 0.0, "riel": 0}

        if usd_match:
            data[today_str]["usd"] += float(usd_match.group(1).replace(",", ""))
        if riel_match:
            data[today_str]["riel"] += int(riel_match.group(1).replace(",", ""))

        save_data(data)
        logging.info(f"Recorded payment for {today_str}: {data[today_str]}")

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

# ===== Simplified /dSum =====
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

    usd_total = 0.0
    riel_total = 0

    for key in keys:
        if key in data:
            usd_total += data[key].get("usd", 0.0)
            riel_total += data[key].get("riel", 0)

    # Reply in simple two-line format
    reply = f"🧾 វិក្កយបត្រ  {usd_total:.2f}   \n💵 ${usd_total:,.2f} | R. {riel_total:,}"
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

    # Message handler to record payments
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, record_payment))

    app.run_polling()

if __name__ == "__main__":
    main()
