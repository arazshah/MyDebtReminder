import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from database import Database
from debt_manager import DebtManager
from reminder_service import ReminderService

# Conversation states
ADDING_DEBT_CATEGORY = 1
ADDING_DEBT_AMOUNT = 2
ADDING_DEBT_DATE = 3
ADDING_DEBT_DESCRIPTION = 4
ADDING_DEBT_RECURRENCE = 5
EDITING_DEBT = 6
ADDING_REMINDER = 7

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
            "   ربات به صورت گام به گام از شما می‌پرسد:\n"
            "   ۱. دسته‌بندی (اجاره، قسطی، برق، گاز، ...)\n"
            "   ۲. مبلغ (به تومان)\n"
            "   ۳. تاریخ سررسید (YYYY-MM-DD)\n"
            "   ۴. توضیحات (اختیاری)\n"
            "   ۵. نوع تکرار (یک بار، ماهانه، هفتگی، سالانه)\n\n"
            "🔸 /list_debts - نمایش تمام بدهی‌های فعال\n"
            "   مرتب شده بر اساس تاریخ سررسید\n\n"
            "🔸 /pay_debt <شناسه> - علامت‌گذاری بدهی به عنوان پرداخت شده\n"
            "   مثال: /pay_debt 1\n\n"
            "🔸 /delete_debt <شناسه> - حذف بدهی\n"
            "   مثال: /delete_debt 1\n\n"
            "🔸 /add_reminder - اضافه کردن یادآور سفارشی\n"
            "   برای رویدادهای غیر بدهی\n\n"
            "🔸 /cancel - لغو عملیات جاری\n\n"
            "📅 یادآورهای خودکار:\n"
            "• ۷ روز قبل از سررسید\n"
            "• ۳ روز قبل از سررسید\n"
            "• ۱ روز قبل از سررسید\n"
            "• در روز سررسید\n\n"
            "💡 نکات:\n"
            "• فرآیند اضافه کردن بدهی کاملاً راهنما شده است\n"
            "• می‌توانید در هر مرحله با /cancel عملیات را لغو کنید\n"
            "• تاریخ را به فرمت YYYY-MM-DD وارد کنید (مثال: 2024-12-25)\n"
        )
        await update.message.reply_text(help_text)

    async def add_debt_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a debt - ask for category"""
        await update.message.reply_text(
            "➕ اضافه کردن بدهی جدید\n\n"
            "مرحله ۱ از ۵: دسته‌بندی\n\n"
            "لطفاً دسته‌بندی بدهی را وارد کنید:\n\n"
            "پیشنهادات:\n"
            "• اجاره\n"
            "• قسطی\n"
            "• برق\n"
            "• گاز\n"
            "• آب\n"
            "• خرید\n"
            "• وام\n"
            "• یا هر دسته‌بندی دیگری که می‌خواهید\n\n"
            "برای لغو عملیات از /cancel استفاده کنید."
        )
        return ADDING_DEBT_CATEGORY

    async def add_debt_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process category and ask for amount"""
        category = update.message.text.strip()
        
        if not category:
            await update.message.reply_text("❌ دسته‌بندی نمی‌تواند خالی باشد. لطفاً دوباره وارد کنید:")
            return ADDING_DEBT_CATEGORY
        
        context.user_data['debt_category'] = category
        
        await update.message.reply_text(
            f"✅ دسته‌بندی: {category}\n\n"
            "مرحله ۲ از ۵: مبلغ\n\n"
            "لطفاً مبلغ بدهی را به تومان وارد کنید:\n\n"
            "مثال: 2000000\n"
            "(فقط عدد، بدون کاما یا نقطه)"
        )
        return ADDING_DEBT_AMOUNT

    async def add_debt_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process amount and ask for due date"""
        text = update.message.text.strip()
        
        try:
            amount = int(text.replace(',', '').replace('،', ''))
            if amount <= 0:
                await update.message.reply_text("❌ مبلغ باید بیشتر از صفر باشد. لطفاً دوباره وارد کنید:")
                return ADDING_DEBT_AMOUNT
            
            context.user_data['debt_amount'] = amount
            
            await update.message.reply_text(
                f"✅ مبلغ: {amount:,} تومان\n\n"
                "مرحله ۳ از ۵: تاریخ سررسید\n\n"
                "لطفاً تاریخ سررسید را وارد کنید:\n\n"
                "فرمت: YYYY-MM-DD\n"
                "مثال: 2024-12-25\n\n"
                "نکته: سال-ماه-روز"
            )
            return ADDING_DEBT_DATE
            
        except ValueError:
            await update.message.reply_text("❌ مبلغ باید عدد باشد. لطفاً دوباره وارد کنید:")
            return ADDING_DEBT_AMOUNT

    async def add_debt_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process due date and ask for description"""
        due_date = update.message.text.strip()
        
        try:
            from datetime import datetime
            datetime.fromisoformat(due_date)
            
            context.user_data['debt_due_date'] = due_date
            
            await update.message.reply_text(
                f"✅ تاریخ سررسید: {due_date}\n\n"
                "مرحله ۴ از ۵: توضیحات\n\n"
                "لطفاً توضیحات بدهی را وارد کنید:\n\n"
                "مثال: اجاره ماهانه آپارتمان\n\n"
                "اگر نمی‌خواهید توضیحات اضافه کنید، عبارت 'ندارد' یا '-' را وارد کنید."
            )
            return ADDING_DEBT_DESCRIPTION
            
        except ValueError:
            await update.message.reply_text(
                "❌ فرمت تاریخ نامعتبر است.\n"
                "لطفاً به فرمت YYYY-MM-DD وارد کنید (مثال: 2024-12-25):"
            )
            return ADDING_DEBT_DATE

    async def add_debt_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process description and ask for recurrence"""
        description = update.message.text.strip()
        
        if description in ['ندارد', '-', 'نداره', 'no', 'none']:
            description = ""
        
        context.user_data['debt_description'] = description
        
        # Create inline keyboard for recurrence options
        keyboard = [
            [
                InlineKeyboardButton("یک بار (one-time)", callback_data="recur_one-time"),
                InlineKeyboardButton("ماهانه (monthly)", callback_data="recur_monthly")
            ],
            [
                InlineKeyboardButton("هفتگی (weekly)", callback_data="recur_weekly"),
                InlineKeyboardButton("سالانه (yearly)", callback_data="recur_yearly")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        desc_text = description if description else "(بدون توضیحات)"
        await update.message.reply_text(
            f"✅ توضیحات: {desc_text}\n\n"
            "مرحله ۵ از ۵: نوع تکرار\n\n"
            "لطفاً نوع تکرار بدهی را انتخاب کنید:",
            reply_markup=reply_markup
        )
        return ADDING_DEBT_RECURRENCE

    async def add_debt_recurrence(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process recurrence and save the debt"""
        query = update.callback_query
        await query.answer()
        
        recurrence = query.data.replace("recur_", "")
        user_id = query.from_user.id
        
        # Get all stored data
        category = context.user_data.get('debt_category')
        amount = context.user_data.get('debt_amount')
        due_date = context.user_data.get('debt_due_date')
        description = context.user_data.get('debt_description', '')
        
        try:
            result = self.debt_manager.add_debt(user_id, category, amount, due_date, description, recurrence)
            
            # Clear user data
            context.user_data.clear()
            
            # Map recurrence to Persian
            recurrence_map = {
                'one-time': 'یک بار',
                'monthly': 'ماهانه',
                'weekly': 'هفتگی',
                'yearly': 'سالانه'
            }
            
            summary = (
                f"✅ بدهی با موفقیت اضافه شد!\n\n"
                f"📋 خلاصه:\n"
                f"• دسته‌بندی: {category}\n"
                f"• مبلغ: {amount:,} تومان\n"
                f"• تاریخ سررسید: {due_date}\n"
                f"• توضیحات: {description if description else '(ندارد)'}\n"
                f"• تکرار: {recurrence_map.get(recurrence, recurrence)}\n\n"
                f"{result}"
            )
            
            await query.edit_message_text(summary)
            
        except Exception as e:
            await query.edit_message_text(f"❌ خطا در ذخیره بدهی: {str(e)}")
        
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
                ADDING_DEBT_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_debt_category)],
                ADDING_DEBT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_debt_amount)],
                ADDING_DEBT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_debt_date)],
                ADDING_DEBT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.add_debt_description)],
                ADDING_DEBT_RECURRENCE: [CallbackQueryHandler(self.add_debt_recurrence, pattern="^recur_")],
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
        self.reminder_service.start_scheduler()

        print("🤖 ربات یادآور بدهی شروع به کار کرد...")
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            # Keep the bot running
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 ربات متوقف شد.")
        finally:
            # Stop reminder service
            if self.reminder_service:
                self.reminder_service.stop_scheduler()
            # Properly shutdown the application
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
