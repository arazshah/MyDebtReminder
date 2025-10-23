import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any
import pytz

class Database:
    def __init__(self, db_path: str = 'data/debts.db'):
        self.db_path = db_path
        self.tehran_tz = pytz.timezone('Asia/Tehran')
        self.init_db()

    def init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create debts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS debts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    due_date TEXT NOT NULL,
                    description TEXT,
                    recurrence TEXT DEFAULT 'one-time',
                    is_paid BOOLEAN DEFAULT FALSE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    paid_at TEXT
                )
            ''')

            # Create reminders table for custom reminders
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    reminder_date TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

    def add_debt(self, user_id: int, category: str, amount: int, due_date: str,
                 description: str = "", recurrence: str = "one-time") -> int:
        """Add a new debt to the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO debts (user_id, category, amount, due_date, description, recurrence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, category, amount, due_date, description, recurrence))
            conn.commit()
            return cursor.lastrowid

    def get_active_debts(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all active (unpaid) debts for a user, sorted by due date"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, category, amount, due_date, description, recurrence
                FROM debts
                WHERE user_id = ? AND is_paid = FALSE
                ORDER BY due_date ASC
            ''', (user_id,))
            rows = cursor.fetchall()

            debts = []
            for row in rows:
                debts.append({
                    'id': row[0],
                    'category': row[1],
                    'amount': row[2],
                    'due_date': row[3],
                    'description': row[4],
                    'recurrence': row[5]
                })
            return debts

    def mark_debt_paid(self, debt_id: int, user_id: int) -> bool:
        """Mark a debt as paid"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE debts
                SET is_paid = TRUE, paid_at = ?
                WHERE id = ? AND user_id = ?
            ''', (datetime.now(self.tehran_tz).isoformat(), debt_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_debt(self, debt_id: int, user_id: int) -> bool:
        """Delete a debt"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM debts
                WHERE id = ? AND user_id = ?
            ''', (debt_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_debt_by_id(self, debt_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific debt by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, category, amount, due_date, description, recurrence, is_paid
                FROM debts
                WHERE id = ? AND user_id = ?
            ''', (debt_id, user_id))
            row = cursor.fetchone()

            if row:
                return {
                    'id': row[0],
                    'category': row[1],
                    'amount': row[2],
                    'due_date': row[3],
                    'description': row[4],
                    'recurrence': row[5],
                    'is_paid': bool(row[6])
                }
            return None

    def get_upcoming_debts(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get debts that are due within the specified number of days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, category, amount, due_date, description
                FROM debts
                WHERE is_paid = FALSE AND date(due_date) <= date('now', '+{} days')
                ORDER BY due_date ASC
            '''.format(days_ahead), ())
            rows = cursor.fetchall()

            debts = []
            for row in rows:
                debts.append({
                    'id': row[0],
                    'user_id': row[1],
                    'category': row[2],
                    'amount': row[3],
                    'due_date': row[4],
                    'description': row[5]
                })
            return debts

    def add_reminder(self, user_id: int, title: str, reminder_date: str,
                     description: str = "") -> int:
        """Add a custom reminder"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO reminders (user_id, title, reminder_date, description)
                VALUES (?, ?, ?, ?)
            ''', (user_id, title, reminder_date, description))
            conn.commit()
            return cursor.lastrowid

    def get_active_reminders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all active reminders for a user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, description, reminder_date
                FROM reminders
                WHERE user_id = ? AND is_active = TRUE
                ORDER BY reminder_date ASC
            ''', (user_id,))
            rows = cursor.fetchall()

            reminders = []
            for row in rows:
                reminders.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'reminder_date': row[3]
                })
            return reminders

    def get_upcoming_reminders(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Get reminders that are due within the specified number of days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, title, description, reminder_date
                FROM reminders
                WHERE is_active = TRUE AND date(reminder_date) <= date('now', '+{} days')
                ORDER BY reminder_date ASC
            '''.format(days_ahead), ())
            rows = cursor.fetchall()

            reminders = []
            for row in rows:
                reminders.append({
                    'id': row[0],
                    'user_id': row[1],
                    'title': row[2],
                    'description': row[3],
                    'reminder_date': row[4]
                })
            return reminders

    def deactivate_reminder(self, reminder_id: int, user_id: int) -> bool:
        """Deactivate a reminder"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE reminders
                SET is_active = FALSE
                WHERE id = ? AND user_id = ?
            ''', (reminder_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
