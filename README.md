# Telegram Bot

This bot replies to the /start command with the user's username, user ID, and group ID (if in a group).

## Deployment on Render

1. Push this repository to GitHub.
2. Go to [Render](https://render.com) and create a new Web Service or Background Worker.
3. Connect your GitHub repository.
4. Choose the `starter` plan ($7/month).
5. Set the environment variable `TELEGRAM_BOT_TOKEN` with your bot token.
6. Render will automatically deploy and run your bot.

## Files

- `telegram_bot.py`: The bot script.
- `requirements.txt`: Python dependencies.
- `render.yaml`: Render deployment configuration.
