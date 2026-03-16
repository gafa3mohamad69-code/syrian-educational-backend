"""
════════════════════════════════════════════════════════════════
    قاعدة البيانات - SQLite
════════════════════════════════════════════════════════════════
"""

import sqlite3
from datetime import datetime
from contextlib import contextmanager
import os

DATABASE_FILE = os.getenv("DATABASE_FILE", "maktabati.db")

@contextmanager
def get_db():
    """الاتصال بقاعدة البيانات"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """تهيئة قاعدة البيانات"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # جدول المستخدمين
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('student', 'teacher', 'library', 'admin')),
                verified BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                UNIQUE(email)
            )
        """)
        
        # جدول المحتويات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                subject TEXT NOT NULL,
                content_type TEXT NOT NULL,
                publisher_email TEXT NOT NULL,
                publisher_role TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                downloads INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (publisher_email) REFERENCES users(email)
            )
        """)
        
        # جدول محاولات الدخول الفاشلة (Rate Limiting)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                ip_address TEXT,
                attempt_time TEXT NOT NULL,
                success BOOLEAN NOT NULL
            )
        """)
        
        # جدول السجلات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                user_email TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        
        conn.commit()

def create_admin_if_not_exists(email: str, password_hash: str):
    """إنشاء حساب المشرف إذا لم يكن موجوداً"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # التحقق من وجود المشرف
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        
        if cursor.fetchone() is None:
            cursor.execute("""
                INSERT INTO users (email, password, first_name, last_name, role, verified, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (email, password_hash, "مشرف", "النظام", "admin", 1, datetime.now().isoformat()))
            
            conn.commit()
            return True
        return False
