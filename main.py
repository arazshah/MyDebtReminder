#!/usr/bin/env python3
"""
ربات یادآور بدهی - Debt Reminder Bot
A Persian Telegram bot for managing debts and reminders
"""

import os
import asyncio
from bot_handler import BotHandler

async def main():
    """Main function to run the bot"""
    # Get bot token from environment variable
    token = os.getenv('TELEGRAM_BOT_TOKEN')

    if not token:
        print("❌ خطا: متغیر محیطی TELEGRAM_BOT_TOKEN تنظیم نشده است.")
        print("لطفاً توکن ربات تلگرام خود را در متغیر محیطی TELEGRAM_BOT_TOKEN قرار دهید.")
        print("مثال:")
        print("export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        return

    # Create bot handler
    bot_handler = BotHandler()

    try:
        # Run the bot
        await bot_handler.run_bot(token)
    except Exception as e:
        print(f"❌ خطا در اجرای ربات: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e):
            # Event loop is already running (e.g., in Jupyter or some environments)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise
