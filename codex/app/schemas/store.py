from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field


class StoreBase(BaseModel):
    name: str = Field(..., max_length=100)
    address: str
    contact_phone: str | None = Field(default=None, max_length=30)
    description: str | None = None
    status: int = 1
    open_time: time = time(hour=8, minute=0)
    close_time: time = time(hour=23, minute=0)


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    address: str | None = None
    contact_phone: str | None = Field(default=None, max_length=30)
    description: str | None = None
    status: int | None = None
    open_time: time | None = None
    close_time: time | None = None


class StoreOut(StoreBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
