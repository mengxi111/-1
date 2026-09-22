from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

ROLE_PATTERN = "^(student|staff|admin|super_admin)$"


class UserBase(BaseModel):
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    name: str = Field(..., max_length=50)
    role: str = Field(..., pattern=ROLE_PATTERN)
    status: int = 1

    @model_validator(mode="after")
    def validate_contact(self) -> "UserBase":
        if not self.phone and not self.email:
            raise ValueError("手机号和邮箱至少填写一项")
        return self


class UserCreate(UserBase):
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserUpdate(BaseModel):
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    name: str | None = Field(default=None, max_length=50)
    role: str | None = Field(default=None, pattern=ROLE_PATTERN)
    password: str | None = Field(default=None, min_length=6, max_length=128)
    status: int | None = None

    @model_validator(mode="after")
    def validate_contact(self) -> "UserUpdate":
        if self.phone is None and self.email is None:
            return self
        if self.phone == "" and self.email == "":
            raise ValueError("手机号和邮箱至少填写一项")
        return self


class UserOut(BaseModel):
    id: int
    phone: str | None
    email: str | None
    name: str
    role: str
    status: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
