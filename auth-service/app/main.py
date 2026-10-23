
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models
from app.database import Base, engine, get_db
from app.schemas import TokenResponse, UserLogin, UserRegister, UserResponse

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

if not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32:
    raise RuntimeError("JWT_SECRET_KEY must contain at least 32 characters")

if ACCESS_TOKEN_EXPIRE_MINUTES < 1:
    raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")

password_hash = PasswordHash.recommended()
oauth2_scheme = HTTPBearer()

app = FastAPI(title="Authentication Service",description="User registration, login, and JWT authentication.",version="1.0.0",)

Base.metadata.create_all(bind=engine)


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)], db: Session = Depends(get_db)) -> models.User:
    token = credentials.credentials
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid or expired access token",headers={"WWW-Authenticate": "Bearer"},)

    try:
        payload = jwt.decode(token,JWT_SECRET_KEY,algorithms=[JWT_ALGORITHM],options={"require": ["sub", "exp", "iat"]},)
        subject = payload.get("sub")

        if not isinstance(subject, str) or not subject.isdigit():
            raise credentials_error

        user_id = int(subject)
    except (InvalidTokenError, ValueError):
        raise credentials_error

    user = db.query(models.User).filter(models.User.id == user_id).first()

    if user is None or not user.is_active:
        raise credentials_error

    return user



@app.post("/auth/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED,)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    email = str(user_data.email).strip().lower()

    existing_user = (db.query(models.User).filter(func.lower(models.User.email) == email).first())

    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="An account with this email already exists",)

    user = models.User(name=user_data.name,email=email,hashed_password=password_hash.hash(user_data.password),)

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail="Unable to register user",)


@app.post("/auth/login", response_model=TokenResponse)
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    email = str(login_data.email).strip().lower()

    user = (db.query(models.User).filter(func.lower(models.User.email) == email).first())

    if user is None or not password_hash.verify(
        login_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid email or password",headers={"WWW-Authenticate": "Bearer"},)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="This account is inactive",)

    return TokenResponse(access_token=create_access_token(user.id))


@app.get("/auth/me", response_model=UserResponse)
def get_my_profile(current_user: Annotated[models.User, Depends(get_current_user)]):
    return current_user
