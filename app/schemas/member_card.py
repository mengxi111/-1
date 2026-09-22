from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MemberCardBase(BaseModel):
    user_id: int
    card_name: str = Field(..., max_length=50)
    card_type: str = Field(..., pattern="^(time|times)$")
    balance_minutes: int = 0
    balance_times: int = 0
    expire_at: date | None = None
    status: str = Field(default="active", pattern="^(active|expired|disabled)$")


class MemberCardCreate(MemberCardBase):
    pass


class MemberCardUpdate(BaseModel):
    user_id: int | None = None
    card_name: str | None = Field(default=None, max_length=50)
    card_type: str | None = Field(default=None, pattern="^(time|times)$")
    balance_minutes: int | None = None
    balance_times: int | None = None
    expire_at: date | None = None
    status: str | None = Field(default=None, pattern="^(active|expired|disabled)$")


class MemberCardOut(MemberCardBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
