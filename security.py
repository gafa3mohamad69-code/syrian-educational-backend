"""
════════════════════════════════════════════════════════════════
    الأمان و Rate Limiting
════════════════════════════════════════════════════════════════
"""

from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from database import get_db
import os

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    """تشفير كلمة المرور"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """التحقق من كلمة المرور"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """إنشاء JWT Token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def check_rate_limit(email: str, max_attempts: int = 5, window_minutes: int = 15) -> tuple:
    """
    التحقق من عدد محاولات الدخول
    
    Returns:
        (allowed: bool, remaining_attempts: int, wait_time: int)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # حساب وقت النافذة
        window_start = (datetime.now() - timedelta(minutes=window_minutes)).isoformat()
        
        # عد المحاولات الفاشلة
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM login_attempts 
            WHERE email = ? 
            AND attempt_time > ? 
            AND success = 0
        """, (email, window_start))
        
        failed_attempts = cursor.fetchone()["count"]
        
        if failed_attempts >= max_attempts:
            # حساب وقت الانتظار
            cursor.execute("""
                SELECT attempt_time 
                FROM login_attempts 
                WHERE email = ? 
                AND success = 0 
                ORDER BY attempt_time DESC 
                LIMIT 1
            """, (email,))
            
            last_attempt = cursor.fetchone()
            if last_attempt:
                last_attempt_time = datetime.fromisoformat(last_attempt["attempt_time"])
                elapsed = (datetime.now() - last_attempt_time).total_seconds() / 60
                wait_time = max(0, window_minutes - int(elapsed))
                
                return False, 0, wait_time
        
        remaining = max_attempts - failed_attempts
        return True, remaining, 0

def log_login_attempt(email: str, success: bool, ip_address: str = None):
    """تسجيل محاولة دخول"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO login_attempts (email, ip_address, attempt_time, success)
            VALUES (?, ?, ?, ?)
        """, (email, ip_address, datetime.now().isoformat(), success))
        conn.commit()
