import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=10, description="Password must be at least 10 characters")
    college: str | None = None
    grad_year: int | None = None
    target_role: str | None = None
    target_companies: list[str] | None = None

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 min in seconds
    user: "UserResponse"

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    college: str | None = None
    grad_year: int | None = None
    target_role: str | None = None
    target_companies: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    college: str | None = None
    grad_year: int | None = None
    target_role: str | None = None
    target_companies: list[str] | None = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=10)
