from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AreaBase(BaseModel):
    store_id: int
    name: str = Field(..., max_length=50)
    code: str = Field(..., max_length=30)
    sort_order: int = 0


class AreaCreate(AreaBase):
    pass


class AreaUpdate(BaseModel):
    store_id: int | None = None
    name: str | None = Field(default=None, max_length=50)
    code: str | None = Field(default=None, max_length=30)
    sort_order: int | None = None


class AreaOut(AreaBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminSeatBase(BaseModel):
    store_id: int
    area_id: int | None = None
    seat_no: str = Field(..., max_length=30)
    seat_type: str = Field(default="normal", max_length=20)
    seat_status: str = Field(default="available", pattern="^(available|maintenance|disabled)$")
    is_available: bool = True


class AdminSeatCreate(AdminSeatBase):
    pass


class AdminSeatUpdate(BaseModel):
    store_id: int | None = None
    area_id: int | None = None
    seat_no: str | None = Field(default=None, max_length=30)
    seat_type: str | None = Field(default=None, max_length=20)
    seat_status: str | None = Field(default=None, pattern="^(available|maintenance|disabled)$")
    is_available: bool | None = None


class AdminSeatOut(AdminSeatBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminSeatBatchCreateIn(BaseModel):
    store_id: int
    area_id: int | None = None
    prefix: str = Field(..., min_length=1, max_length=10, description="座位号前缀，例如 A")
    start_no: int = Field(default=1, ge=1, le=9999)
    end_no: int = Field(..., ge=1, le=9999)
    padding: int = Field(default=2, ge=1, le=6, description="数字位数补零")
    seat_type: str = Field(default="normal", max_length=20)
    seat_status: str = Field(default="available", pattern="^(available|maintenance|disabled)$")
    is_available: bool = True


class AdminSeatBatchCreateOut(BaseModel):
    created_count: int
    skipped_count: int
    seat_nos: list[str]


class PlanBase(BaseModel):
    store_id: int
    name: str = Field(..., max_length=100)
    billing_type: str = Field(..., pattern="^(hour|day|month)$")
    price: Decimal
    min_minutes: int = 30
    max_minutes: int = 720
    status: str = Field(default="active", pattern="^(active|inactive)$")


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    store_id: int | None = None
    name: str | None = Field(default=None, max_length=100)
    billing_type: str | None = Field(default=None, pattern="^(hour|day|month)$")
    price: Decimal | None = None
    min_minutes: int | None = None
    max_minutes: int | None = None
    status: str | None = Field(default=None, pattern="^(active|inactive)$")


class PlanOut(PlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: int
    booking_id: int
    user_id: int
    amount: Decimal | float
    status: str
    created_at: datetime
    updated_at: datetime
    store_id: int | None = None
    store_name: str | None = None
    user_name: str | None = None
    user_phone: str | None = None
    booking_status: str | None = None
    seat_no: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class OrderPageOut(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[OrderOut]


class OrderActionOut(BaseModel):
    order_id: int
    status: str


class AdminBookingOut(BaseModel):
    id: int
    user_id: int
    seat_id: int
    start_time: datetime
    end_time: datetime
    status: str
    checked_in_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MembershipOpenIn(BaseModel):
    user_id: int
    card_name: str = Field(..., max_length=50)
    card_type: str = Field(..., pattern="^(time|times)$")
    balance_minutes: int = 0
    balance_times: int = 0
    expire_at: date | None = None


class MembershipRenewIn(BaseModel):
    add_minutes: int = 0
    add_times: int = 0
    extend_days: int = 0


class MembershipFreezeIn(BaseModel):
    frozen: bool = True


class MembershipOut(BaseModel):
    id: int
    user_id: int
    card_name: str
    card_type: str
    balance_minutes: int
    balance_times: int
    expire_at: date | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BootstrapOut(BaseModel):
    stores_created: int
    areas_created: int
    seats_created: int
    plans_created: int
    message: str


class BootstrapDemoOut(BootstrapOut):
    users_created: int
    bookings_created: int
    orders_created: int
    notices_created: int
    notifications_created: int


class BlacklistCreateIn(BaseModel):
    user_id: int
    reason: str | None = Field(default=None, max_length=255)


class BlacklistActionOut(BaseModel):
    user_id: int
    blacklisted: bool
    message: str


class BlacklistOut(BaseModel):
    id: int
    user_id: int
    reason: str
    source: str
    is_active: bool
    start_at: datetime
    end_at: datetime | None
    no_show_count_snapshot: int | None
    created_by: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingReleaseLogOut(BaseModel):
    id: int
    booking_id: int
    user_id: int
    seat_id: int
    release_type: str
    reason: str
    remark: str | None
    released_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OperationLogOut(BaseModel):
    id: int
    operator_id: int | None
    operator_name: str | None
    operator_role: str | None
    ip: str
    module: str
    request_method: str
    request_path: str
    status_code: int
    content: str
    summary: str | None = None
    duration_ms: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OperationLogPageOut(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[OperationLogOut]


class CheckinRecordOut(BaseModel):
    id: int
    booking_id: int
    user_id: int
    seat_id: int
    store_id: int | None
    checkin_time: datetime
    checkin_method: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CheckinRecordPageOut(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[CheckinRecordOut]


class AdminUserListOut(BaseModel):
    id: int
    phone: str | None
    email: str | None
    name: str
    role: str
    status: int
    no_show_count: int = 0
    is_blacklisted: bool = False
    blacklist_end_at: datetime | None = None
    history_booking_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminUserDetailOut(AdminUserListOut):
    last_booking_at: datetime | None = None


class AdminUserRoleAssignIn(BaseModel):
    role: str = Field(..., pattern="^(student|staff|admin|super_admin)$")


class AdminUserRoleAssignOut(BaseModel):
    user_id: int
    role: str
    role_text: str


class SystemConfigOut(BaseModel):
    min_booking_minutes: int
    max_booking_hours: int
    cancel_before_minutes: int
    reschedule_before_minutes: int
    checkin_grace_minutes: int
    no_show_blacklist_threshold: int
    blacklist_effective_days: int
    default_open_time: str
    default_close_time: str


class SystemConfigUpdateIn(BaseModel):
    min_booking_minutes: int | None = Field(default=None, ge=1, le=720)
    max_booking_hours: int | None = Field(default=None, ge=1, le=24)
    cancel_before_minutes: int | None = Field(default=None, ge=0, le=1440)
    reschedule_before_minutes: int | None = Field(default=None, ge=0, le=1440)
    checkin_grace_minutes: int | None = Field(default=None, ge=1, le=240)
    no_show_blacklist_threshold: int | None = Field(default=None, ge=1, le=20)
    blacklist_effective_days: int | None = Field(default=None, ge=1, le=365)
    default_open_time: str | None = Field(default=None, pattern="^\\d{2}:\\d{2}$")
    default_close_time: str | None = Field(default=None, pattern="^\\d{2}:\\d{2}$")
