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
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
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
        "username": username,
        "timestamp": datetime.now().isoformat()
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

# ===== Record all messages (both user and bot) =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Skip if message is edited
    if update.edited_message:
        return
        
    text = update.message.text or ""
    invoice_matches = invoice_pattern.findall(text)
    total_match = total_pattern.search(text)
    
    if invoice_matches and total_match:
        try:
            usd_amount = float(total_match.group(1).replace(",", ""))
            riel_amount = int(total_match.group(2).replace(",", ""))
            
            # Determine sender info
            if update.message.from_user.is_bot:
                user_id = 0
                username = "Bot"
            else:
                user_id = update.effective_user.id
                username = update.effective_user.username or f"User_{user_id}"
            
            # Record each invoice number found
            for inv in invoice_matches:
                record_invoice(inv, usd_amount, riel_amount, user_id, username)
                
        except (ValueError, AttributeError) as e:
            logging.error(f"Error processing invoice message: {e}")

# ===== /Sum command =====
async def sum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today_str = datetime.now().strftime("%Y-%m-%d")
    data = load_data()
    invoices = data.get(today_str, [])

    if not invoices:
        await update.message.reply_text("No invoices recorded today.")
        return

    # Calculate totals
    usd_total = sum(inv["usd"] for inv in invoices)
    riel_total = sum(inv["riel"] for inv in invoices)

    # Prepare response
    lines = []
    for inv in invoices:
        source = "🤖 Bot" if inv["user_id"] == 0 else f"👤 {inv['username']}"
        lines.append(f"{source} - 🧾 វិក្កយបត្រ {inv['invoice_no']}")
        lines.append(f"💵 ${inv['usd']:,.2f} | R. {inv['riel']:,}")
    
    lines.append("_______________________")
    lines.append(f"📊 សរុបថ្ងៃនេះ:")
    lines.append(f"💵 ${usd_total:,.2f} | R. {riel_total:,}")
    lines.append(f"📝 ចំនួនសរុប: {len(invoices)} វិក័យប័ត្រ")

    await update.message.reply_text("\n".join(lines))

# ===== Main =====
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logging.error("No TELEGRAM_BOT_TOKEN environment variable found!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("Sum", sum_command))

    # Handle all text messages (from both users and bots)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    logging.info("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
