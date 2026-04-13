from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models.user import User
from app.schemas.auth import (
    AuthTokenResponse,
    LoginRequest,
    SignupRequest,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# MVP placeholder: real auth will delegate to Supabase Auth (GoTrue).
# For now we return a deterministic token based on user id to unblock the UI.


@router.post("/signup", response_model=AuthTokenResponse)
async def signup(
    req: SignupRequest,
    session: Session = Depends(get_session),
) -> AuthTokenResponse:
    existing = session.exec(select(User).where(User.email == req.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="email already registered")
    user = User(email=req.email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return AuthTokenResponse(access_token=f"dev-{user.id}", user_id=user.id)


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    req: LoginRequest,
    session: Session = Depends(get_session),
) -> AuthTokenResponse:
    user = session.exec(select(User).where(User.email == req.email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return AuthTokenResponse(access_token=f"dev-{user.id}", user_id=user.id)


@router.get("/me", response_model=UserOut)
async def me(
    user_id: UUID,
    session: Session = Depends(get_session),
) -> UserOut:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return UserOut(id=user.id, email=user.email, created_at=user.created_at)
