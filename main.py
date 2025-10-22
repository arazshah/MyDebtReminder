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
    except KeyboardInterrupt:
        print("\n🛑 ربات متوقف شد.")
    except Exception as e:
        print(f"❌ خطا در اجرای ربات: {e}")
    finally:
        # Stop reminder service if it exists
        if bot_handler.reminder_service:
            await bot_handler.reminder_service.stop_scheduler()

if __name__ == '__main__':
    asyncio.run(main())
