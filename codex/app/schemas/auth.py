from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    phone: str = Field(..., max_length=20)
    name: str = Field(..., max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    phone: str = Field(..., max_length=20)
    password: str = Field(..., min_length=6, max_length=128)


class AuthUserOut(BaseModel):
    id: int
    phone: str | None
    email: str | None = None
    name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserOut
