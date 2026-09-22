from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "自习室管理系统"
    environment: str = "development"
    auto_seed_demo: bool = True
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/study_room"
    timezone: str = "Asia/Shanghai"
    redis_url: str = "redis://localhost:6380/0"
    redis_lock_ttl_ms: int = 10000
    redis_lock_required: bool = False
    checkin_code_expire_minutes: int = 10
    checkin_qr_expire_minutes: int = 3
    checkin_grace_minutes: int = 30
    min_booking_minutes: int = 30
    max_booking_hours: int = 12
    allow_booking_start_in_past: bool = False
    cancel_before_minutes: int = 30
    reschedule_before_minutes: int = 60
    no_show_blacklist_threshold: int = 3
    blacklist_effective_days: int = 7
    default_store_open_time: str = "08:00"
    default_store_close_time: str = "23:00"
    order_module_enabled: bool = False
    reminder_minutes_before_start: int = 30
    expire_job_interval_seconds: int = 300
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_days: int = 14
    email_enabled: bool = False
    smtp_host: str | None = None
    smtp_port: int = 465
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_ssl: bool = True
    smtp_use_tls: bool = False
    smtp_timeout_seconds: int = 15
    smtp_from_email: str | None = None
    smtp_from_name: str = "自习室管理系统"
    email_send_batch_size: int = 50
    email_job_interval_seconds: int = 60

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.environment.lower() != "production":
            return self
        if self.auto_seed_demo:
            raise ValueError("生产环境必须设置 AUTO_SEED_DEMO=false")
        if self.jwt_secret_key == "change-this-in-production" or len(self.jwt_secret_key) < 32:
            raise ValueError("生产环境必须配置至少 32 位的 JWT_SECRET_KEY")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
