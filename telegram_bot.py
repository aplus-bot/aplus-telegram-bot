import logging
import os
import re
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ===== Logging Setup =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)
logger = logging.getLogger(__name__)

# ===== Data Management =====
DATA_FILE = "daily_invoices.json"

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading data: {e}")
    return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving data: {e}")

def record_invoice(invoice_no, usd, riel, user_id, username, chat_id):
    today_str = datetime.now().strftime("%Y-%m-%d")
    data = load_data()
    
    if today_str not in data:
        data[today_str] = {}
    if str(chat_id) not in data[today_str]:
        data[today_str][str(chat_id)] = []
        
    data[today_str][str(chat_id)].append({
        "invoice_no": invoice_no,
        "usd": usd,
        "riel": riel,
        "user_id": user_id,
        "username": username,
        "timestamp": datetime.now().isoformat(),
        "is_bot": user_id == 0  # True if message is from bot
    })
    save_data(data)
    logger.info(f"Invoice recorded - Chat:{chat_id} Invoice:{invoice_no} ${usd}|R{riel} by {'Bot' if user_id == 0 else username}")

# ===== Message Patterns =====
invoice_pattern = re.compile(r"🧾\s*វិក្កយបត្រ\s*(\d+)")
total_pattern = re.compile(r"💵\s*សរុប\s*:\s*\$([\d,.]+)\s*\|\s*R\.\s*([\d,]+)")

# ===== Command Handlers =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Hello {user.first_name}!\n"
        f"UserID: {user.id}\n"
        f"Username: @{user.username if user.username else 'N/A'}"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Available commands:\n"
        "/start - Show your info\n"
        "/help - This help message\n"
        "/sum - Show today's invoices (group only)\n"
        "/about - About this bot"
    )

# ===== Core Message Handler =====
async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.edited_message or not update.message or not update.message.text:
        return
        
    text = update.message.text
    chat_id = update.effective_chat.id
    
    # Check if message is an invoice
    invoice_nos = invoice_pattern.findall(text)
    total_match = total_pattern.search(text)
    
    if invoice_nos and total_match:
        try:
            usd = float(total_match.group(1).replace(",", ""))
            riel = int(total_match.group(2).replace(",", ""))
            
            # Determine sender
            if update.message.from_user.is_bot:
                user_id = 0
                username = "Bot"
            else:
                user_id = update.effective_user.id
                username = update.effective_user.username or f"User_{user_id}"
            
            # Record all invoice numbers found
            for inv_no in invoice_nos:
                record_invoice(inv_no, usd, riel, user_id, username, chat_id)
                
            logger.debug(f"Processed invoice message in chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Failed to process invoice: {e}")

# ===== Sum Command (Group Only) =====
async def sum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    
    # Restrict to groups only
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ This command only works in groups!")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    chat_id = str(chat.id)
    data = load_data()
    
    # Get today's invoices for this specific group
    group_invoices = data.get(today, {}).get(chat_id, [])
    
    if not group_invoices:
        await update.message.reply_text("📭 No invoices recorded today in this group.")
        return

    # Calculate totals
    usd_total = sum(inv["usd"] for inv in group_invoices)
    riel_total = sum(inv["riel"] for inv in group_invoices)
    bot_invoices = sum(1 for inv in group_invoices if inv.get("is_bot"))
    user_invoices = len(group_invoices) - bot_invoices

    # Prepare summary
    summary = [
        "📊 Today's Invoice Summary",
        "------------------------",
        f"🤖 Bot Invoices: {bot_invoices}",
        f"👤 User Invoices: {user_invoices}",
        "------------------------",
        f"💵 Total USD: ${usd_total:,.2f}",
        f"៛ Total Riel: R{riel_total:,}",
        "------------------------",
        f"📝 Total Invoices: {len(group_invoices)}"
    ]

    await update.message.reply_text("\n".join(summary))

# ===== Main Application =====
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("Missing TELEGRAM_BOT_TOKEN!")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("sum", sum_command))

    # Handle all text messages (including bot's own messages)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_all_messages
    ))

    logger.info("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
