from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional

import os
from dotenv import load_dotenv

load_dotenv()

# Secret keys and algorithms
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-for-development-only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# --- Mock Email Dispatcher ---
# In production, replace this with smtplib and a real SMTP server.
def send_email(to_email: str, subject: str, body: str):
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"--- MOCK EMAIL ---")
    logger.warning(f"To: {to_email}")
    logger.warning(f"Subject: {subject}")
    logger.warning(f"Body: {body}")
    logger.warning(f"------------------")
