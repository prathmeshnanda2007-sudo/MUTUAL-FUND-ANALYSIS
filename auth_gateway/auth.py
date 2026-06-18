from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Secret keys and algorithms
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set. Please check your .env file.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# SMTP configuration (read from environment)
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME)

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


def send_email(to_email: str, subject: str, body: str) -> bool:
    """
    Send an email via SMTP.

    Reads SMTP credentials from environment variables:
        SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_FROM_EMAIL

    Falls back to a warning log if SMTP is not configured (development mode).

    Returns:
        True if email was sent successfully, False otherwise.
    """
    if not SMTP_HOST or not SMTP_USERNAME or not SMTP_PASSWORD:
        # Development fallback — log the email instead of failing silently
        logger.warning("SMTP not configured. Email would have been sent:")
        logger.warning(f"  To:      {to_email}")
        logger.warning(f"  Subject: {subject}")
        logger.warning(f"  Body:    {body}")
        logger.warning(
            "Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, "
            "SMTP_FROM_EMAIL in your .env to enable real email delivery."
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM_EMAIL
        msg["To"] = to_email

        # Plain-text part
        text_part = MIMEText(body, "plain")

        # HTML part (wraps body in a simple styled template)
        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #1e293b; padding: 24px;">
            <div style="max-width: 520px; margin: auto; background: #f8fafc;
                        border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px;">
              <h2 style="color: #0f172a; margin-bottom: 16px;">Bluestock MF Analytics</h2>
              <p style="line-height: 1.7; white-space: pre-line;">{body}</p>
              <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
              <p style="font-size: 12px; color: #94a3b8;">
                This email was sent by Bluestock MF Analytics Platform.
                If you did not request this, please ignore it.
              </p>
            </div>
          </body>
        </html>
        """
        html_part = MIMEText(html_body, "html")

        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM_EMAIL, to_email, msg.as_string())

        logger.info(f"Email sent successfully to {to_email} | Subject: {subject}")
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed. Check SMTP_USERNAME and SMTP_PASSWORD.")
    except smtplib.SMTPConnectError:
        logger.error(f"Failed to connect to SMTP server {SMTP_HOST}:{SMTP_PORT}.")
    except smtplib.SMTPRecipientsRefused:
        logger.error(f"Recipient refused by SMTP server: {to_email}")
    except Exception as e:
        logger.error(f"Unexpected error while sending email to {to_email}: {e}")

    return False
