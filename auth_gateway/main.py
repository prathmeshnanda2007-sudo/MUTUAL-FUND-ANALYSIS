from fastapi import FastAPI, Depends, HTTPException, status, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import uuid
import secrets
import os
from dotenv import load_dotenv
from authlib.integrations.starlette_client import OAuth
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()

from auth_gateway.database import get_db
from auth_gateway.models import User, PasswordReset
from auth_gateway.auth import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    send_email,
    SECRET_KEY
)

app = FastAPI()

# Setup CORS — origins loaded from env var (comma-separated list)
_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8501,http://127.0.0.1:8501,http://localhost:5173,http://127.0.0.1:5173"
)
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.mount("/static", StaticFiles(directory="auth_gateway/static"), name="static")
templates = Jinja2Templates(directory="auth_gateway/templates")

STREAMLIT_URL = os.getenv("STREAMLIT_URL", "http://localhost:8501").rstrip("/")
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"

# --- Google OAuth Setup ---
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse(request=request, name="landing.html", context={})

@app.get("/api/platform-stats")
async def platform_stats(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text
        # Count total unique mutual funds
        funds_count = db.execute(text("SELECT COUNT(DISTINCT amfi_code) FROM dim_fund")).scalar()
        # Get average 1-year returns
        avg_returns = db.execute(text("SELECT AVG(return_1yr) FROM fact_performance")).scalar()
        
        return {
            "fundsTracked": funds_count or 0,
            "avgReturns": round(avg_returns, 2) if avg_returns else 0.0,
            "activeUsers": 2450  # Hardcoded example for live users
        }
    except Exception as e:
        return {"fundsTracked": 12500, "avgReturns": 15.4, "activeUsers": 2450}

@app.get("/login", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})

@app.post("/login", response_class=HTMLResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return templates.TemplateResponse(request=request, name="login.html", context={
            "error": "No account found with this email address. Please create an account first."
        })
    
    if not user.password_hash or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(request=request, name="login.html", context={
            "error": "Incorrect password. Please try again."
        })
        
    user.last_login = datetime.utcnow()
    db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "name": user.full_name}, expires_delta=access_token_expires
    )

    response = RedirectResponse(url=STREAMLIT_URL, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=IS_PRODUCTION 
    )
    return response

@app.get("/register", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={"error": None})

@app.post("/register", response_class=HTMLResponse)
@limiter.limit("3/minute")
async def register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "Passwords do not match."})
        
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return templates.TemplateResponse(request=request, name="register.html", context={
            "error": "An account with this email address is already registered. Please log in instead."
        })
        
    hashed_password = get_password_hash(password)
    new_user = User(
        full_name=full_name,
        email=email,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email, "name": new_user.full_name}, expires_delta=access_token_expires
    )

    response = RedirectResponse(url=STREAMLIT_URL, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=IS_PRODUCTION
    )
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

@app.get("/forgot-password", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(request=request, name="forgot_password.html", context={"msg": None, "error": None})

@app.post("/forgot-password", response_class=HTMLResponse)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if user:
        token = secrets.token_urlsafe(32)
        reset = PasswordReset(
            email=email,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(reset)
        db.commit()
        
        auth_base_url = os.getenv("AUTH_BASE_URL", "http://localhost:8000").rstrip("/")
        reset_link = f"{auth_base_url}/reset-password?token={token}"
        send_email(
            to_email=email,
            subject="Password Reset — Bluestock MF Analytics",
            body=(
                f"Hello,\n\n"
                f"You requested a password reset for your Bluestock MF Analytics account.\n\n"
                f"Click the link below to reset your password (expires in 1 hour):\n"
                f"{reset_link}\n\n"
                f"If you did not request this, please ignore this email."
            )
        )
        
    return templates.TemplateResponse(request=request, name="forgot_password.html", context={
        "msg": "If your email is registered, you will receive a password reset link shortly.",
        "error": None
    })

@app.get("/reset-password", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def reset_password_page(request: Request, token: str):
    return templates.TemplateResponse(request=request, name="reset_password.html", context={"token": token, "error": None})

@app.post("/reset-password", response_class=HTMLResponse)
@limiter.limit("3/minute")
async def reset_password(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        return templates.TemplateResponse(request=request, name="reset_password.html", context={"token": token, "error": "Passwords do not match."})
        
    reset_entry = db.query(PasswordReset).filter(
        PasswordReset.token == token,
        PasswordReset.is_used == False,
        PasswordReset.expires_at > datetime.utcnow()
    ).first()
    
    if not reset_entry:
        return templates.TemplateResponse(request=request, name="reset_password.html", context={"token": token, "error": "Invalid or expired reset token."})
        
    user = db.query(User).filter(User.email == reset_entry.email).first()
    if not user:
        return templates.TemplateResponse(request=request, name="reset_password.html", context={"token": token, "error": "User not found."})
        
    if user.password_hash and verify_password(password, user.password_hash):
        return templates.TemplateResponse(request=request, name="reset_password.html", context={"token": token, "error": "New password cannot be the same as the current password."})

    user.password_hash = get_password_hash(password)
    reset_entry.is_used = True
    db.commit()
    
    return templates.TemplateResponse(request=request, name="login.html", context={
        "error": None,
        "success_msg": "Your password has been successfully updated. Please log in with your new password."
    })

# --- Google OAuth REAL Flow ---
@app.get("/auth/google")
async def google_auth(request: Request):
    redirect_uri = request.url_for('google_auth_callback')
    return await oauth.google.authorize_redirect(request, str(redirect_uri))

@app.get("/auth/google/callback")
async def google_auth_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        return templates.TemplateResponse(request=request, name="login.html", context={"error": f"OAuth Error: {str(e)}"})

    user_info = token.get('userinfo')
    if not user_info:
        user_info = await oauth.google.parse_id_token(request, token)
        
    email = user_info.get("email")
    name = user_info.get("name")
    google_id = user_info.get("sub")
    picture = user_info.get("picture")

    if not email:
        return templates.TemplateResponse(request=request, name="login.html", context={"error": "Failed to get email from Google."})

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            full_name=name,
            email=email,
            is_email_verified=True,
            google_account_id=google_id,
            profile_picture_url=picture
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not user.google_account_id:
            user.google_account_id = google_id
            user.is_email_verified = True
        if picture and not user.profile_picture_url:
            user.profile_picture_url = picture
            
    user.last_login = datetime.utcnow()
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "name": user.full_name}, expires_delta=access_token_expires
    )

    response = RedirectResponse(url=STREAMLIT_URL, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=IS_PRODUCTION
    )
    return response

