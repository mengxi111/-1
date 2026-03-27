from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class AuthUser(BaseModel):
    id: int
    role: str
    nickname: str
    phone: str | None = None
    email: str | None = None


class RegisterIn(BaseModel):
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    nickname: str = Field(..., max_length=50)

    @model_validator(mode="after")
    def validate_contact(self) -> "RegisterIn":
        if not self.phone and not self.email:
            raise ValueError("手机号和邮箱至少填写一项")
        return self


class LoginIn(BaseModel):
    account: str = Field(..., max_length=255, description="手机号或邮箱")
    password: str = Field(..., min_length=6, max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str


class LogoutIn(BaseModel):
    refresh_token: str


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_expires_in: int
    refresh_expires_at: datetime
    user: AuthUser


class LogoutOut(BaseModel):
    success: bool
