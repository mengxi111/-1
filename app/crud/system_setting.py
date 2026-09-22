from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.system_setting import SystemSetting


BOOKING_RULE_DEFAULTS: dict[str, tuple[int, str]] = {
    "min_booking_minutes": (settings.min_booking_minutes, "最短预约时长（分钟）"),
    "max_booking_hours": (settings.max_booking_hours, "最长预约时长（小时）"),
    "cancel_before_minutes": (settings.cancel_before_minutes, "预约开始前可取消分钟数"),
    "reschedule_before_minutes": (settings.reschedule_before_minutes, "预约开始前可改期分钟数"),
    "checkin_grace_minutes": (settings.checkin_grace_minutes, "开始后签到宽限分钟数"),
    "no_show_blacklist_threshold": (settings.no_show_blacklist_threshold, "爽约达到阈值后自动拉黑"),
}

SYSTEM_CONFIG_DEFAULTS: dict[str, tuple[int | str, str]] = {
    **BOOKING_RULE_DEFAULTS,
    "blacklist_effective_days": (settings.blacklist_effective_days, "黑名单生效天数"),
    "default_open_time": (settings.default_store_open_time, "默认营业开始时间"),
    "default_close_time": (settings.default_store_close_time, "默认营业结束时间"),
}


def get_setting(db: Session, key: str) -> SystemSetting | None:
    return db.execute(select(SystemSetting).where(SystemSetting.key == key)).scalar_one_or_none()


def get_setting_int(db: Session, key: str, default: int) -> int:
    setting = get_setting(db, key)
    if setting is None:
        return default
    try:
        value = int(setting.value)
    except (TypeError, ValueError):
        return default
    return value


def get_setting_str(db: Session, key: str, default: str) -> str:
    setting = get_setting(db, key)
    if setting is None or setting.value is None or setting.value == "":
        return default
    return str(setting.value)


def get_booking_rule_config(db: Session) -> dict[str, int]:
    data: dict[str, int] = {}
    for key, (default_value, _) in BOOKING_RULE_DEFAULTS.items():
        data[key] = get_setting_int(db, key, default_value)
    return data


def get_system_config(db: Session) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for key, (default_value, _) in SYSTEM_CONFIG_DEFAULTS.items():
        if isinstance(default_value, int):
            data[key] = get_setting_int(db, key, default_value)
        else:
            data[key] = get_setting_str(db, key, default_value)
    return data


def upsert_settings(
    db: Session,
    *,
    values: Mapping[str, int | str],
    commit: bool = True,
) -> dict[str, int | str]:
    updated: dict[str, int | str] = {}
    for key, raw_value in values.items():
        if key not in SYSTEM_CONFIG_DEFAULTS:
            continue
        default_value, description = SYSTEM_CONFIG_DEFAULTS[key]
        value = int(raw_value) if isinstance(default_value, int) else str(raw_value)
        setting = get_setting(db, key)
        if setting is None:
            setting = SystemSetting(
                key=key,
                value=str(value),
                description=description or f"默认值：{default_value}",
            )
        else:
            setting.value = str(value)
            if not setting.description:
                setting.description = description
        db.add(setting)
        updated[key] = value
    if commit:
        db.commit()
    else:
        db.flush()
    return updated


def reset_settings_to_defaults(db: Session, *, commit: bool = True) -> dict[str, Any]:
    defaults = {key: default for key, (default, _) in SYSTEM_CONFIG_DEFAULTS.items()}
    upsert_settings(db, values=defaults, commit=commit)
    return get_system_config(db)
