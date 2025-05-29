from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from argon2 import PasswordHasher #argon2 for password hashing
from argon2.exceptions import VerifyMismatchError

from pathlib import Path
import shutil
import os
import traceback

from stt import transcribe_file

#password reset
import secrets
from datetime import datetime, timedelta

from models import User, SessionLocal , PasswordResetToken#models.py file

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

ph = PasswordHasher()

app = FastAPI()

# Enable CORS to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

base_dir = Path(__file__).parent

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the login.html file directly"""#changed this to serve the login.html file directly
    try:
        html_path = base_dir / "login.html"
        with open(html_path, "r", encoding="utf-8") as html_file:
            return html_file.read()
    except Exception as e:
        return HTMLResponse(content=f"<html><body><h1>Error loading login.html</h1><p>{str(e)}</p></body></html>", 
                           status_code=500)
    
@app.get("/login", response_class=HTMLResponse)
async def get_login():
    html_path = base_dir / "login.html"
    with open(html_path, "r", encoding="utf-8") as html_file:
        return html_file.read()

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    try:
        ph.verify(user.hashed_password, password)  # Use argon2 to verify
    except VerifyMismatchError:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": "Login successful", "username": username}

    
@app.get("/index", response_class=HTMLResponse)
async def get_index():
    html_path = base_dir / "index.html"
    with open(html_path, "r", encoding="utf-8") as html_file:
        return html_file.read()

#DATABASE SETUP


@app.post("/register")
async def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = ph.hash(password)
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}


@app.post("/request-password-reset")
async def request_password_reset(username: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        # Always respond with success to avoid leaking user existence
        return {"message": "If this email exists, a reset link was sent."}
    # Generate secure token
    token = secrets.token_urlsafe(64)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    # Store token
    db.add(PasswordResetToken(user_id=user.id, token=token, expires_at=expires_at))
    db.commit()
    # TODO: Send email to user with link (e.g., http://yourdomain/reset-password?token=...)
    print(f"Password reset link: http://localhost:8000/reset-password?token={token}")
    return {"message": "If this username exists, a reset link was sent."}

@app.post("/reset-password")
async def reset_password(token: str = Form(...), new_password: str = Form(...), db: Session = Depends(get_db)):
    prt = db.query(PasswordResetToken).filter(PasswordResetToken.token == token).first()
    if not prt or prt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == prt.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    user.hashed_password = ph.hash(new_password)
    db.delete(prt)  # Remove used token
    db.commit()
    return {"message": "Password reset successfully"}

@app.get("/reset-password", response_class=HTMLResponse)
async def get_reset_password():
    html_path = base_dir / "reset_password.html"
    with open(html_path, "r", encoding="utf-8") as html_file:
        return html_file.read()
