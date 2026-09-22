from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BookingCreate(BaseModel):
    seat_id: int
    start_time: datetime
    end_time: datetime
    user_id: int | None = None

    @model_validator(mode="after")
    def validate_time_window(self) -> "BookingCreate":
        if self.end_time <= self.start_time:
            raise ValueError("开始时间必须早于结束时间")
        return self


class BookingCreateResponse(BaseModel):
    booking_id: int
    status: str


class BookingCheckinRequest(BaseModel):
    verification_code: str | None = Field(default=None, min_length=6, max_length=6)


class BookingCheckinResponse(BaseModel):
    booking_id: int
    status: str
    message: str
    verification_code: str | None = None


class BookingOut(BaseModel):
    id: int
    user_id: int
    seat_id: int
    start_time: datetime
    end_time: datetime
    status: str
    checkin_code_expires_at: datetime | None
    checked_in_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
