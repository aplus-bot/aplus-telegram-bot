import logging
import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging to a file
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)

# A dictionary to store the running totals for each group chat
# This will keep track of sums over a period of time.
group_totals = {}

# /start command handler
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

# /help command handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = (
        "Available commands:\n"
        "/start - Show user info\n"
        "/help - List available commands\n"
        "/about - About this bot\n"
        "/sum - Show the total amount collected\n"
        "/reset - Reset the total for this group"
    )
    await update.message.reply_text(response)
    user = update.effective_user
    chat = update.effective_chat
    logging.info(f"/help used by {user.username} ({user.id}) in chat {chat.id}")

# /about command handler
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = (
        "About SystemBot:\n"
        "1) [Teacher Ngov Samnang](https://t.me/Aplus_SD)\n"
        "2) [Contruction or Using](https://t.me/AplusSD_V5/194)\n"
        "3) [On Youtube](https://www.youtube.com/playlist?list=PLikM0v0bp6Cg8MC9hUnsZn9RU450YmFn0)"
    )
    await update.message.reply_text(response, disable_web_page_preview=True)
    user = update.effective_user
    chat = update.effective_chat
    logging.info(f"/about used by {user.username} ({user.id}) in chat {chat.id}")

# /sum command handler
async def sum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in group_totals:
        total_usd = group_totals[chat_id]['usd']
        total_khr = group_totals[chat_id]['khr']

        reply_message = (
            f"**💵 Current Total**\n"
            f"-----------------------------------\n"
            f"💰 **Total (USD):** ${total_usd:,.2f}\n"
            f"💰 **Total (KHR):** R. {total_khr:,.0f}\n"
            f"-----------------------------------"
        )
        await update.message.reply_text(reply_message, parse_mode='Markdown')
        logging.info(f"/sum command used by {update.effective_user.username} ({update.effective_user.id}) in chat {chat_id}. Totals: USD {total_usd}, KHR {total_khr}")
    else:
        await update.message.reply_text("❌ No invoices have been processed in this group yet.")
        logging.info(f"/sum command used, but no totals found for group {chat_id}")

# /reset command handler
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in group_totals:
        # Reset the totals for the current group
        group_totals[chat_id] = {'usd': 0.0, 'khr': 0.0}
        await update.message.reply_text("✅ The totals for this group have been reset.")
        logging.info(f"Totals reset by {update.effective_user.username} ({update.effective_user.id}) for group {chat_id}")
    else:
        await update.message.reply_text("❌ No totals to reset for this group.")

# Message handler to read and sum invoices
async def sum_invoices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message_text = update.message.text

    # Make sure the message is a bill from MS Access
    if '🧾 វិក្កយបត្រ' in message_text and '💵 សរុប' in message_text:
        # Get or initialize the totals for the current group
        if chat_id not in group_totals:
            group_totals[chat_id] = {'usd': 0.0, 'khr': 0.0}

        # Use a regular expression to find the dollar and Riel amounts
        usd_match = re.search(r'\$\s*(\d+\.\d{2})', message_text)
        khr_match = re.search(r'R\.\s*([\d,]+)', message_text)

        usd_amount = 0.0
        khr_amount = 0.0

        if usd_match:
            usd_amount = float(usd_match.group(1))
            group_totals[chat_id]['usd'] += usd_amount
            logging.info(f"Extracted ${usd_amount} from message in group {chat_id}")

        if khr_match:
            # Remove commas from the Riel amount before converting to float
            khr_amount = float(khr_match.group(1).replace(',', ''))
            group_totals[chat_id]['khr'] += khr_amount
            logging.info(f"Extracted R. {khr_amount} from message in group {chat_id}")

        # Construct and send the new reply message
        total_usd = group_totals[chat_id]['usd']
        total_khr = group_totals[chat_id]['khr']

        reply_message = (
            f"**🧾 Total Sum so far**\n"
            f"-----------------------------------\n"
            f"💵 **Total (USD):** ${total_usd:,.2f}\n"
            f"💵 **Total (KHR):** R. {total_khr:,.0f}\n"
            f"-----------------------------------"
        )

        await update.message.reply_text(reply_message, parse_mode='Markdown')
        logging.info(f"Sent summary reply in group {chat_id}")

# Main function to run the bot
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logging.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    # Add the command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CommandHandler("sum", sum_command)) # New command handler
    app.add_handler(CommandHandler("reset", reset_command))

    # Add the message handler to process invoices
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), sum_invoices))

    logging.info("Bot is starting to poll...")
    app.run_polling()

# Run the bot
if __name__ == "__main__":
    main()
