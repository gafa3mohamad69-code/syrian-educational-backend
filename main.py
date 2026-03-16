from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from jose import jwt
from typing import Optional
import sqlite3
import hashlib
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = "syria-edu-secret-2025"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440
DATABASE_FILE = "syria_edu.db"

app = FastAPI(title="مجتمع سوريا التعليمية API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تشفير سريع جداً!
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hashlib.sha256(plain.encode()).hexdigest() == hashed

def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            user_type TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Content table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            content_type TEXT NOT NULL,
            stage TEXT NOT NULL,
            subject TEXT NOT NULL,
            uploader_id INTEGER NOT NULL,
            views INTEGER DEFAULT 0,
            downloads INTEGER DEFAULT 0,
            average_rating REAL DEFAULT 0.0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uploader_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("✅ Database initialized")

init_db()

class UserCreate(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)
    password: str = Field(..., min_length=8)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    user_type: str
    is_active: bool
    created_at: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

@app.get("/")
async def root():
    return {"message": "مرحباً!", "version": "2.0"}

@app.post("/api/auth/register/student", response_model=Token)
async def register_student(user: UserCreate):
    try:
        logger.info(f"📝 Registration: {user.email}")

        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        if cursor.fetchone():
            conn.close()
            logger.warning(f"❌ Email exists: {user.email}")
            raise HTTPException(status_code=400, detail="البريد مسجل مسبقاً")

        logger.info("🔒 Hashing password...")
        hashed = hash_password(user.password)
        logger.info("✅ Password hashed (fast!)")

        cursor.execute(
            "INSERT INTO users (email, hashed_password, first_name, last_name, user_type) VALUES (?, ?, ?, ?, 'student')",
            (user.email, hashed, user.first_name, user.last_name)
        )
        conn.commit()
        user_id = cursor.lastrowid

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = dict(cursor.fetchone())
        conn.close()

        token = jwt.encode({"sub": user_id}, SECRET_KEY, algorithm=ALGORITHM)

        user_resp = UserResponse(
            id=row['id'],
            email=row['email'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            user_type=row['user_type'],
            is_active=bool(row['is_active']),
            created_at=str(row['created_at'])
        )

        logger.info(f"🎉 Registration successful: {user.email}")

        return Token(access_token=token, token_type="bearer", user=user_resp)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login", response_model=Token)
async def login(data: LoginRequest):
    try:
        logger.info(f"🔐 Login: {data.email}")

        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (data.email,))
        row = cursor.fetchone()
        conn.close()

        if not row or not verify_password(data.password, row['hashed_password']):
            raise HTTPException(status_code=401, detail="البريد أو كلمة المرور خطأ")

        user_dict = dict(row)
        token = jwt.encode({"sub": user_dict['id']}, SECRET_KEY, algorithm=ALGORITHM)

        user_resp = UserResponse(
            id=user_dict['id'],
            email=user_dict['email'],
            first_name=user_dict['first_name'],
            last_name=user_dict['last_name'],
            user_type=user_dict['user_type'],
            is_active=bool(user_dict['is_active']),
            created_at=str(user_dict['created_at'])
        )

        logger.info(f"✅ Login successful: {data.email}")

        return Token(access_token=token, token_type="bearer", user=user_resp)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/content")
async def get_content(
    skip: int = 0,
    limit: int = 20,
    stage: Optional[str] = None,
    subject: Optional[str] = None
):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM content WHERE is_active = 1"
        params = []

        if stage:
            query += " AND stage = ?"
            params.append(stage)
        if subject:
            query += " AND subject = ?"
            params.append(subject)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, skip])

        cursor.execute(query, params)
        content_list = [dict(row) for row in cursor.fetchall()]
        conn.close()

        logger.info(f"✅ Fetched {len(content_list)} content items")
        return content_list

    except Exception as e:
        logger.error(f"💥 Error fetching content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/content/{content_id}")
async def get_content_by_id(content_id: int):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM content WHERE id = ? AND is_active = 1", (content_id,))
        content = cursor.fetchone()

        if not content:
            conn.close()
            raise HTTPException(status_code=404, detail="المحتوى غير موجود")

        cursor.execute("UPDATE content SET views = views + 1 WHERE id = ?", (content_id,))
        conn.commit()

        result = dict(content)
        result['views'] = result['views'] + 1
        conn.close()

        logger.info(f"✅ Content {content_id} fetched")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
