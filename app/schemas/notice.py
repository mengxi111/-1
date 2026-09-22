from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


NOTICE_STATUS_PATTERN = "^(draft|published|offline)$"


class NoticeBase(BaseModel):
    store_id: int | None = None
    title: str = Field(..., max_length=200)
    content: str


class NoticeCreate(NoticeBase):
    status: str = Field(default="draft", pattern=NOTICE_STATUS_PATTERN)


class NoticeUpdate(BaseModel):
    store_id: int | None = None
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None
    status: str | None = Field(default=None, pattern=NOTICE_STATUS_PATTERN)


class NoticeOut(BaseModel):
    id: int
    store_id: int | None
    title: str
    content: str
    status: str
    published_at: datetime | None
    created_by: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NoticeDetailOut(NoticeOut):
    store_name: str | None = None
    created_by_name: str | None = None


class StudentNoticeItemOut(BaseModel):
    id: int
    store_id: int | None
    store_name: str | None = None
    title: str
    content: str
    status: str
    published_at: datetime | None
    created_at: datetime


class NoticeActionOut(BaseModel):
    id: int
    status: str
    status_text: str
