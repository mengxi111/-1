from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StudentBookingCreateIn(BaseModel):
    seat_id: int
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_time_window(self) -> "StudentBookingCreateIn":
        if self.end_time <= self.start_time:
            raise ValueError("开始时间必须早于结束时间")
        return self


class StudentBookingCreateOut(BaseModel):
    booking_id: int
    status: str


class StudentBookingCancelOut(BaseModel):
    booking_id: int
    status: str


class StudentStoreOut(BaseModel):
    id: int
    name: str
    address: str

    model_config = ConfigDict(from_attributes=True)


class StudentSeatOut(BaseModel):
    id: int
    store_id: int
    area_id: int | None
    seat_no: str
    seat_type: str
    seat_status: str
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


class StudentBookingOut(BaseModel):
    id: int
    user_id: int
    seat_id: int
    start_time: datetime
    end_time: datetime
    status: str
    checked_in_at: datetime | None = None
    can_checkin: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentBookingRescheduleIn(BaseModel):
    seat_id: int | None = None
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_time_window(self) -> "StudentBookingRescheduleIn":
        if self.end_time <= self.start_time:
            raise ValueError("开始时间必须早于结束时间")
        return self


class StudentQrCheckinCreateOut(BaseModel):
    booking_id: int
    status: str
    qr_token: str
    qr_content: str
    qr_expires_at: datetime
    message: str


class StudentQrCheckinConfirmIn(BaseModel):
    qr_token: str = Field(..., min_length=8, max_length=128)


class StudentQrCheckinConfirmOut(BaseModel):
    booking_id: int
    status: str
    checked_in_at: datetime | None
    message: str


class StudentMyReservationItemOut(BaseModel):
    reservation_id: int
    store_name: str
    seat_no: str
    start_time: datetime
    end_time: datetime
    status: str
    can_sign_in: bool


class StudentMyReservationListOut(BaseModel):
    code: int = 200
    message: str = "操作成功"
    data: list[StudentMyReservationItemOut]


class StudentSignInDataOut(BaseModel):
    reservation_id: int
    status: str
    sign_in_time: datetime


class StudentSignInOut(BaseModel):
    code: int = 200
    message: str = "签到成功"
    data: StudentSignInDataOut
