from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import pytz
from typing import Dict, Any, List
from database import Database
from debt_manager import DebtManager

class ReminderService:
    def __init__(self, bot, db: Database, debt_manager: DebtManager):
        self.bot = bot
        self.db = db
        self.debt_manager = debt_manager
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone('Asia/Tehran'))
        self.tehran_tz = pytz.timezone('Asia/Tehran')

    async def start_scheduler(self):
        """Start the reminder scheduler"""
        self.scheduler.start()
        await self.schedule_daily_reminders()

    async def schedule_daily_reminders(self):
        """Schedule daily reminder checks"""
        # Run reminder check every day at 9 AM Tehran time
        self.scheduler.add_job(
            self.send_daily_reminders,
            trigger=CronTrigger(hour=9, minute=0, timezone=self.tehran_tz),
            id='daily_reminders',
            replace_existing=True
        )

    async def send_daily_reminders(self):
        """Send reminders for upcoming debts"""
        try:
            # Get debts due in the next 7 days
            upcoming_debts = self.debt_manager.get_upcoming_reminders(7)

            # Group debts by user
            user_debts = {}
            for debt in upcoming_debts:
                user_id = debt['user_id']
                if user_id not in user_debts:
                    user_debts[user_id] = []
                user_debts[user_id].append(debt)

            # Send reminders to each user
            for user_id, debts in user_debts.items():
                await self.send_user_reminders(user_id, debts)

        except Exception as e:
            print(f"Error sending daily reminders: {e}")

    async def send_user_reminders(self, user_id: int, debts: List[Dict[str, Any]]):
        """Send reminders to a specific user"""
        try:
            for debt in debts:
                days_until_due = self.calculate_days_until_due(debt['due_date'])

                # Only send reminders for debts due within 7 days, 3 days, 1 day, or today
                if days_until_due <= 7:
                    message = self.debt_manager.get_reminder_message(debt, days_until_due)
                    await self.bot.send_message(chat_id=user_id, text=message)

        except Exception as e:
            print(f"Error sending reminder to user {user_id}: {e}")

    def calculate_days_until_due(self, due_date_str: str) -> int:
        """Calculate days until due date"""
        try:
            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            if due_date.tzinfo is None:
                due_date = self.tehran_tz.localize(due_date)
            else:
                due_date = due_date.astimezone(self.tehran_tz)

            now = datetime.now(self.tehran_tz)
            days_diff = (due_date.date() - now.date()).days
            return max(0, days_diff)  # Return 0 if already due or overdue
        except:
            return 999  # If date parsing fails, don't send reminder

    async def send_custom_reminders(self):
        """Send custom reminders"""
        try:
            # Get reminders due today or in the next few days
            upcoming_reminders = self.db.get_upcoming_reminders(1)  # Next 24 hours

            for reminder in upcoming_reminders:
                user_id = reminder['user_id']
                title = reminder['title']
                description = reminder['description']

                message = f"🔔 یادآور سفارشی:\n📌 {title}"
                if description:
                    message += f"\n📝 {description}"

                await self.bot.send_message(chat_id=user_id, text=message)

                # Deactivate the reminder after sending
                self.db.deactivate_reminder(reminder['id'], user_id)

        except Exception as e:
            print(f"Error sending custom reminders: {e}")

    async def stop_scheduler(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
