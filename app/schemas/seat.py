from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SeatBase(BaseModel):
    store_id: int
    area_id: int | None = None
    seat_no: str = Field(..., max_length=30)
    seat_type: str = Field(default="normal", max_length=20)
    seat_status: str = Field(default="available", pattern="^(available|maintenance|disabled)$")
    is_available: bool = True


class SeatCreate(SeatBase):
    pass


class SeatUpdate(BaseModel):
    store_id: int | None = None
    area_id: int | None = None
    seat_no: str | None = Field(default=None, max_length=30)
    seat_type: str | None = Field(default=None, max_length=20)
    seat_status: str | None = Field(default=None, pattern="^(available|maintenance|disabled)$")
    is_available: bool | None = None


class SeatOut(SeatBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
