from typing import Dict, Any, List
from datetime import datetime, timedelta
import pytz
from database import Database

class DebtManager:
    def __init__(self, db: Database):
        self.db = db
        self.tehran_tz = pytz.timezone('Asia/Tehran')

    def format_amount(self, amount: int) -> str:
        """Format amount in Iranian Rial with proper separators"""
        return f"{amount:,}"

    def format_date(self, date_str: str) -> str:
        """Format date for display in Persian"""
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if date_obj.tzinfo is None:
                date_obj = self.tehran_tz.localize(date_obj)
            else:
                date_obj = date_obj.astimezone(self.tehran_tz)

            # Persian date format: YYYY/MM/DD
            return date_obj.strftime('%Y/%m/%d')
        except:
            return date_str

    def validate_debt_data(self, category: str, amount: int, due_date: str,
                          description: str = "", recurrence: str = "one-time") -> str:
        """Validate debt input data and return error message if invalid"""
        if not category.strip():
            return "دسته‌بندی نمی‌تواند خالی باشد."

        if amount <= 0:
            return "مبلغ باید بزرگتر از صفر باشد."

        try:
            # Try to parse the date
            datetime.fromisoformat(due_date.replace('Z', '+00:00'))
        except:
            return "فرمت تاریخ نامعتبر است. از فرمت YYYY-MM-DD استفاده کنید."

        valid_recurrences = ["one-time", "monthly", "weekly", "yearly"]
        if recurrence not in valid_recurrences:
            return "نوع تکرار نامعتبر است."

        return ""

    def add_debt(self, user_id: int, category: str, amount: int, due_date: str,
                 description: str = "", recurrence: str = "one-time") -> str:
        """Add a new debt and return success/error message"""
        error = self.validate_debt_data(category, amount, due_date, description, recurrence)
        if error:
            return f"خطا: {error}"

        try:
            debt_id = self.db.add_debt(user_id, category.strip(), amount, due_date,
                                     description.strip(), recurrence)
            return f"✅ بدهی جدید با موفقیت اضافه شد.\nشناسه: {debt_id}"
        except Exception as e:
            return f"خطا در ذخیره بدهی: {str(e)}"

    def get_debts_text(self, user_id: int) -> str:
        """Get formatted text of all active debts"""
        debts = self.db.get_active_debts(user_id)

        if not debts:
            return "📝 هیچ بدهی فعالی ندارید."

        text = "📋 لیست بدهی‌های فعال:\n\n"

        for debt in debts:
            text += f"🆔 {debt['id']}\n"
            text += f"📂 دسته: {debt['category']}\n"
            text += f"💰 مبلغ: {self.format_amount(debt['amount'])} تومان\n"
            text += f"📅 سررسید: {self.format_date(debt['due_date'])}\n"
            if debt['description']:
                text += f"📝 توضیح: {debt['description']}\n"
            text += f"🔄 تکرار: {self.get_recurrence_text(debt['recurrence'])}\n"
            text += "─" * 30 + "\n"

        return text

    def get_recurrence_text(self, recurrence: str) -> str:
        """Convert recurrence to Persian text"""
        recurrence_map = {
            "one-time": "یک بار",
            "weekly": "هفتگی",
            "monthly": "ماهانه",
            "yearly": "سالانه"
        }
        return recurrence_map.get(recurrence, recurrence)

    def mark_paid(self, debt_id: int, user_id: int) -> str:
        """Mark a debt as paid"""
        debt = self.db.get_debt_by_id(debt_id, user_id)
        if not debt:
            return "❌ بدهی یافت نشد."

        if debt['is_paid']:
            return "✅ این بدهی قبلاً پرداخت شده است."

        success = self.db.mark_debt_paid(debt_id, user_id)
        if success:
            return f"✅ بدهی {debt_id} به عنوان پرداخت شده علامت‌گذاری شد."
        else:
            return "❌ خطا در بروزرسانی وضعیت بدهی."

    def delete_debt(self, debt_id: int, user_id: int) -> str:
        """Delete a debt"""
        debt = self.db.get_debt_by_id(debt_id, user_id)
        if not debt:
            return "❌ بدهی یافت نشد."

        success = self.db.delete_debt(debt_id, user_id)
        if success:
            return f"🗑️ بدهی {debt_id} حذف شد."
        else:
            return "❌ خطا در حذف بدهی."

    def get_upcoming_reminders(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get debts that need reminders"""
        return self.db.get_upcoming_debts(days_ahead)

    def get_reminder_message(self, debt: Dict[str, Any], days_until_due: int) -> str:
        """Generate reminder message based on days until due"""
        amount_formatted = self.format_amount(debt['amount'])
        category = debt['category']
        due_date_formatted = self.format_date(debt['due_date'])

        if days_until_due == 0:
            return f"🚨 یادآور: {category} به مبلغ {amount_formatted} تومان سررسید شده است.\n📅 تاریخ سررسید: {due_date_formatted}"
        elif days_until_due == 1:
            return f"⚠️ یادآور: {category} به مبلغ {amount_formatted} تومان فردا سررسید می‌شود.\n📅 تاریخ سررسید: {due_date_formatted}"
        elif days_until_due <= 3:
            return f"🔔 یادآور: {category} به مبلغ {amount_formatted} تومان در {days_until_due} روز آینده سررسید می‌شود.\n📅 تاریخ سررسید: {due_date_formatted}"
        elif days_until_due <= 7:
            return f"📅 یادآور: {category} به مبلغ {amount_formatted} تومان در {days_until_due} روز آینده سررسید می‌شود.\n📅 تاریخ سررسید: {due_date_formatted}"
        else:
            return f"📝 یادآور: {category} به مبلغ {amount_formatted} تومان در تاریخ {due_date_formatted} سررسید می‌شود."
