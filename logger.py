"""
════════════════════════════════════════════════════════════════
    نظام السجلات
════════════════════════════════════════════════════════════════
"""

import logging
from datetime import datetime
from database import get_db
import os

# إعداد الـ Logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("MaktabatiAPI")

def log_to_db(level: str, message: str, user_email: str = None):
    """تسجيل في قاعدة البيانات"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO logs (level, message, user_email, timestamp)
                VALUES (?, ?, ?, ?)
            """, (level, message, user_email, datetime.now().isoformat()))
            conn.commit()
    except:
        pass  # لا نريد أن يتعطل التطبيق بسبب خطأ في التسجيل

def log_info(message: str, user_email: str = None):
    """تسجيل معلومة"""
    logger.info(message)
    log_to_db("INFO", message, user_email)

def log_error(message: str, user_email: str = None):
    """تسجيل خطأ"""
    logger.error(message)
    log_to_db("ERROR", message, user_email)

def log_warning(message: str, user_email: str = None):
    """تسجيل تحذير"""
    logger.warning(message)
    log_to_db("WARNING", message, user_email)
