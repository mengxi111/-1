from datetime import datetime

from pydantic import BaseModel


class StudentNotificationItemOut(BaseModel):
    id: int
    title: str
    content: str
    notification_type: str
    notification_type_text: str
    is_read: bool
    read_at: datetime | None
    email_status: str
    email_error: str | None
    emailed_at: datetime | None
    related_type: str | None
    related_id: int | None
    created_at: datetime


class StudentNotificationListOut(BaseModel):
    total: int
    unread_count: int
    items: list[StudentNotificationItemOut]


class StudentNotificationReadAllOut(BaseModel):
    updated_count: int
