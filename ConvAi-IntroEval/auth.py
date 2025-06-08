from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from argon2 import PasswordHasher, exceptions
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

import models
from models import get_db

# Security configuration
SECRET_KEY = "your-secret-key"  # Change this to a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ph = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)

async def get_token_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if token:
        if token.startswith("Bearer "):
            return token[7:]  # Remove "Bearer " prefix
        return token
    return None

def verify_password(plain_password, hashed_password):
    try:
        return ph.verify(hashed_password, plain_password)
    except exceptions.VerifyMismatchError:
        return False

def get_password_hash(password):
    return ph.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_teacher(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # First try to get token from cookie
    cookie_token = await get_token_from_cookie(request)
    
    # Use cookie token if available, otherwise use Authorization header token
    token_to_verify = cookie_token if cookie_token else token
    
    if not token_to_verify:
        raise credentials_exception
        
    try:
        payload = jwt.decode(token_to_verify, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    teacher = db.query(models.Teacher).filter(
        models.Teacher.username == username
    ).first()
    
    if teacher is None:
        raise credentials_exception
    
    return {"username": teacher.username}

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Retrieve the current authenticated user (student or teacher) based on JWT token.
    This function is used to identify the user's roll number for file organization.
    
    Args:
        request: FastAPI request object
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User or Teacher object if authenticated, None otherwise
    """
    try:
        # First try to get token from cookie
        cookie_token = await get_token_from_cookie(request)
        
        # Use cookie token if available, otherwise use Authorization header token
        token_to_verify = cookie_token if cookie_token else token
        
        if not token_to_verify:
            return None
            
        # Decode JWT token to extract username
        payload = jwt.decode(token_to_verify, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
            
    except JWTError:
        return None

    # First try to find teacher with this username
    teacher = db.query(models.Teacher).filter(
        models.Teacher.username == username
    ).first()
    
    if teacher:
        return teacher
    
    # If not a teacher, try to find student user
    user = db.query(models.User).filter(
        models.User.username == username
    ).first()
    
    return user  # Will be None if neither teacher nor user found
