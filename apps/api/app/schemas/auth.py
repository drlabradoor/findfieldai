from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID


class UserOut(BaseModel):
    id: UUID
    email: str
    created_at: datetime
