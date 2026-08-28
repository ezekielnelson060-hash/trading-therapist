from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Optional

from app.core.database import get_db, engine
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.models import User
from app.services.drip import maybe_send_drip, DRIP
from app.core.config import settings

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    plan: str

    class Config:
        from_attributes = True


@router.get("/db-check")
async def db_check():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        return {"db": "ok", "message": "Connected to database", "build": "ssl-drip-v1"}
    except Exception as e:
        return {"db": "error", "type": type(e).__name__, "message": str(e)}


@router.post("/register", response_model=UserOut)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.email == user_in.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            email=user_in.email,
            hashed_password=hash_password(user_in.password),
            full_name=user_in.full_name,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        try:
            await maybe_send_drip(db, user)
        except Exception:
            pass
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error on register: {type(e).__name__}: {e}",
        )


@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(User).where(User.email == user_in.email))
        user = result.scalar_one_or_none()
        if not user or not user.hashed_password or not verify_password(user_in.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        token = create_access_token(subject=user.id)
        try:
            await maybe_send_drip(db, user)
        except Exception:
            pass
        return Token(access_token=token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error on login: {type(e).__name__}: {e}",
        )


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/drip/process")
async def process_drip_for_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    day = await maybe_send_drip(db, current_user)
    return {
        "sent_day": day,
        "drip_emails_sent": getattr(current_user, "drip_emails_sent", 0),
        "available_days": sorted(DRIP.keys()),
        "resend_configured": bool(settings.RESEND_API_KEY),
    }
