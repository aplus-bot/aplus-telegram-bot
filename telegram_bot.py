import os
import logging
import re
import asyncio
from datetime import datetime, timedelta
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
api_id = 23435657
api_hash = '8d513f47e0492d0b2c4717e74a433364'
session_name = 'aplus_bot_session'
tele_client = TelegramClient(session_name, api_id, api_hash)

# ===== Regex patterns =====
invoice_pattern = re.compile(r"🧾\s*វិក្កយបត្រ\s*(\d+)")
total_pattern = re.compile(r"💵\s*សរុប\s*:\s*\$([\d,.]+)\s*\|\s*R\.\s*([\d,]+)")

# ===== Fetch invoices from a group =====
async def fetch_invoices(group, period="today"):
    usd_total = 0.0
    riel_total = 0
    invoice_lines = []

    today = datetime.now().date()
    dates = []

    if period == "today":
        dates = [today]
    elif period == "yesterday":
        dates = [today - timedelta(days=1)]
    elif period == "week":
        dates = [today - timedelta(days=i) for i in range(7)]
    else:
        return "Invalid period. Use: today, yesterday, week"

    async for message in tele_client.iter_messages(group, limit=1000):
        text = message.text or ""
        msg_date = message.date.date()
        if msg_date not in dates:
            continue

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

    return "\n".join(invoice_lines) if invoice_lines else f"No invoices found for {period}."

# ===== Bot commands =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    await update.message.reply_text(
        f"Hello {user.first_name}!\nUserID: {user.id}\nUserName: {user.username}\nGroupID: {chat.id if chat.type in ['group', 'supergroup'] else 'N/A'}"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n/start\n/help\n/about\n/sum <group_id or username> [today|yesterday|week]"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "About SystemBot:\n1) [Teacher Ngov Samnang](https://t.me/Aplus_SD)\n"
        "2) [Construction or Using](https://t.me/AplusSD_V5/194)\n"
        "3) [On Youtube](https://www.youtube.com/playlist?list=PLikM0v0bp6Cg8MC9hUnsZn9RU450YmFn0)"
    )

async def sum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /sum <group_id or username> [today|yesterday|week]")
        return

    group_input = context.args[0]
    period = context.args[1].lower() if len(context.args) > 1 else "today"

    try:
        group_entity = await tele_client.get_entity(group_input)
    except Exception as e:
        await update.message.reply_text(f"Failed to access group: {e}")
        return

    invoice_text = await fetch_invoices(group_entity, period)
    await update.message.reply_text(invoice_text)

# ===== Main =====
async def main():
    await tele_client.start()
    print("Telethon client started")

    # Telegram bot
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("sum", sum_command))

    # Run bot polling concurrently with Telethon
    await asyncio.gather(
        app.run_polling(),
        asyncio.sleep(0)  # keep the loop alive
    )

if __name__ == "__main__":
    asyncio.run(main())
