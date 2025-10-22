import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from database import Database
from debt_manager import DebtManager
from reminder_service import ReminderService

# Conversation states
ADDING_DEBT = 1
EDITING_DEBT = 2
ADDING_REMINDER = 3

class BotHandler:
    def __init__(self):
        self.db = Database()
        self.debt_manager = DebtManager(self.db)
        self.application = None
        self.reminder_service = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_text = (
            "🤖 به ربات یادآور بدهی خوش آمدید!\n\n"
            "این ربات به شما کمک می‌کند بدهی‌های خود را مدیریت کنید و یادآورهای خودکار دریافت کنید.\n\n"
            "📋 دستورات موجود:\n"
            "/add_debt - اضافه کردن بدهی جدید\n"
            "/list_debts - نمایش لیست بدهی‌ها\n"
            "/pay_debt - پرداخت بدهی\n"
            "/delete_debt - حذف بدهی\n"
            "/add_reminder - اضافه کردن یادآور سفارشی\n"
            "/help - راهنمای استفاده\n\n"
            "برای شروع، از دستور /add_debt استفاده کنید."
        )
        await update.message.reply_text(welcome_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "📖 راهنمای استفاده از ربات یادآور بدهی:\n\n"
            "🔸 /add_debt - اضافه کردن بدهی جدید\n"
            "   مراحل: دسته‌بندی، مبلغ، تاریخ سررسید، توضیحات، نوع تکرار\n\n"
            "🔸 /list_debts - نمایش تمام بدهی‌های فعال\n"
            "   مرتب شده بر اساس تاریخ سررسید\n\n"
            "🔸 /pay_debt <شناسه> - علامت‌گذاری بدهی به عنوان پرداخت شده\n"
            "   مثال: /pay_debt 1\n\n"
            "🔸 /delete_debt <شناسه> - حذف بدهی\n"
            "   مثال: /delete_debt 1\n\n"
            "🔸 /add_reminder - اضافه کردن یادآور سفارشی\n"
            "   برای رویدادهای غیر بدهی\n\n"
            "📅 یادآورهای خودکار:\n"
            "• ۷ روز قبل از سررسید\n"
            "• ۳ روز قبل از سررسید\n"
            "• ۱ روز قبل از سررسید\n"
            "• در روز سررسید\n\n"
            "💡 نکات:\n"
            "• تمام مبالغ به تومان وارد شوند\n"
            "• تاریخ را به فرمت YYYY-MM-DD وارد کنید\n"
            "• دسته‌بندی‌های پیشنهادی: اجاره، قسطی، برق/گاز، خرید\n"
        )
        await update.message.reply_text(help_text)

    async def add_debt_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a debt"""
        await update.message.reply_text(
            "➕ اضافه کردن بدهی جدید\n\n"
            "لطفاً اطلاعات را به فرمت زیر وارد کنید:\n"
            "دسته‌بندی,مبلغ,تاریخ سررسید,توضیحات,تکرار\n\n"
            "مثال:\n"
            "اجاره,۲۰۰۰۰۰۰,۲۰۲۴-۱۲-۰۱,اجاره ماهانه آپارتمان,monthly\n\n"
            "نکات:\n"
            "• دسته‌بندی: اجاره، قسطی، برق، گاز، خرید، یا هر چیز دیگر\n"
            "• مبلغ: به تومان (بدون کاما)\n"
            "• تاریخ: YYYY-MM-DD\n"
            "• تکرار: one-time (یک بار)، monthly (ماهانه)، weekly (هفتگی)، yearly (سالانه)\n"
            "• توضیحات اختیاری است"
        )
        return ADDING_DEBT

    async def add_debt_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process debt addition"""
        user_id = update.effective_user.id
        text = update.message.text.strip()

        try:
            # Parse the input
            parts = [part.strip() for part in text.split(',')]
            if len(parts) < 3:
                await update.message.reply_text("❌ فرمت ورودی نامعتبر. لطفاً از فرمت صحیح استفاده کنید.")
                return ADDING_DEBT

            category = parts[0]
            amount = int(parts[1])
            due_date = parts[2]
            description = parts[3] if len(parts) > 3 else ""
            recurrence = parts[4] if len(parts) > 4 else "one-time"

            result = self.debt_manager.add_debt(user_id, category, amount, due_date, description, recurrence)
            await update.message.reply_text(result)

        except ValueError:
            await update.message.reply_text("❌ مبلغ باید عدد باشد.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")

        return ConversationHandler.END

    async def list_debts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all active debts"""
        user_id = update.effective_user.id
        text = self.debt_manager.get_debts_text(user_id)

        # Create inline keyboard for actions
        keyboard = []
        debts = self.db.get_active_debts(user_id)

        if debts:
            # Group debts in pairs for keyboard
            for i in range(0, len(debts), 2):
                row = []
                for j in range(2):
                    if i + j < len(debts):
                        debt = debts[i + j]
                        row.append(InlineKeyboardButton(
                            f"پرداخت {debt['id']}",
                            callback_data=f"pay_{debt['id']}"
                        ))
                        row.append(InlineKeyboardButton(
                            f"حذف {debt['id']}",
                            callback_data=f"delete_{debt['id']}"
                        ))
                if row:
                    keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        await update.message.reply_text(text, reply_markup=reply_markup)

    async def pay_debt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mark a debt as paid"""
        user_id = update.effective_user.id

        if not context.args:
            await update.message.reply_text("❌ لطفاً شناسه بدهی را وارد کنید.\nمثال: /pay_debt 1")
            return

        try:
            debt_id = int(context.args[0])
            result = self.debt_manager.mark_paid(debt_id, user_id)
            await update.message.reply_text(result)
        except ValueError:
            await update.message.reply_text("❌ شناسه بدهی باید عدد باشد.")

    async def delete_debt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete a debt"""
        user_id = update.effective_user.id

        if not context.args:
            await update.message.reply_text("❌ لطفاً شناسه بدهی را وارد کنید.\nمثال: /delete_debt 1")
            return

        try:
            debt_id = int(context.args[0])
            result = self.debt_manager.delete_debt(debt_id, user_id)
            await update.message.reply_text(result)
        except ValueError:
            await update.message.reply_text("❌ شناسه بدهی باید عدد باشد.")

    async def add_reminder_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a custom reminder"""
        await update.message.reply_text(
            "🔔 اضافه کردن یادآور سفارشی\n\n"
            "لطفاً اطلاعات را به فرمت زیر وارد کنید:\n"
            "عنوان,تاریخ یادآور,توضیحات\n\n"
            "مثال:\n"
            "تماس با شرکت بیمه,۲۰۲۴-۱۲-۱۵,برای تمدید بیمه نامه\n\n"
            "نکات:\n"
            "• عنوان: عنوان یادآور\n"
            "• تاریخ: YYYY-MM-DD\n"
            "• توضیحات اختیاری است"
        )
        return ADDING_REMINDER

    async def add_reminder_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process reminder addition"""
        user_id = update.effective_user.id
        text = update.message.text.strip()

        try:
            parts = [part.strip() for part in text.split(',')]
            if len(parts) < 2:
                await update.message.reply_text("❌ فرمت ورودی نامعتبر.")
                return ADDING_REMINDER

            title = parts[0]
            reminder_date = parts[1]
            description = parts[2] if len(parts) > 2 else ""

            # Validate date
            from datetime import datetime
            datetime.fromisoformat(reminder_date)

            reminder_id = self.db.add_reminder(user_id, title, reminder_date, description)
            await update.message.reply_text(f"✅ یادآور سفارشی اضافه شد.\nشناسه: {reminder_id}")

        except ValueError:
            await update.message.reply_text("❌ فرمت تاریخ نامعتبر.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطا: {str(e)}")

        return ConversationHandler.END

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button presses"""
        query = update.callback_query
        await query.answer()

        user_id = query.from_user.id
        data = query.data

        if data.startswith("pay_"):
            debt_id = int(data.split("_")[1])
            result = self.debt_manager.mark_paid(debt_id, user_id)
            await query.edit_message_text(f"{query.message.text}\n\n{result}")

        elif data.startswith("delete_"):
            debt_id = int(data.split("_")[1])
            result = self.debt_manager.delete_debt(debt_id, user_id)
            await query.edit_message_text(f"{query.message.text}\n\n{result}")

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        await update.message.reply_text("❌ عملیات لغو شد.")
        return ConversationHandler.END

    def setup_handlers(self):
        """Setup all command and conversation handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("list_debts", self.list_debts))
        self.application.add_handler(CommandHandler("pay_debt", self.pay_debt))
        self.application.add_handler(CommandHandler("delete_debt", self.delete_debt))

        # Conversation handlers
        add_debt_conv = ConversationHandler(
            entry_points=[CommandHandler("add_debt", self.add_debt_start)],
            states={
                ADDING_DEBT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_debt_process)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        add_reminder_conv = ConversationHandler(
            entry_points=[CommandHandler("add_reminder", self.add_reminder_start)],
            states={
                ADDING_REMINDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_reminder_process)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )

        self.application.add_handler(add_debt_conv)
        self.application.add_handler(add_reminder_conv)

        # Callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

    async def run_bot(self, token: str):
        """Run the bot"""
        self.application = Application.builder().token(token).build()
        self.reminder_service = ReminderService(self.application.bot, self.db, self.debt_manager)

        self.setup_handlers()

        # Start reminder service
        await self.reminder_service.start_scheduler()

        print("🤖 ربات یادآور بدهی شروع به کار کرد...")
        await self.application.run_polling()
