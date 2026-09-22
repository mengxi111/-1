import json

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.middleware.admin_operation_log import _safe_body_preview, _safe_query_preview


def test_admin_log_redacts_nested_secrets():
    body = json.dumps(
        {
            "name": "student",
            "password": "plain-text-password",
            "session": {"refresh_token": "refresh-secret"},
        }
    ).encode("utf-8")

    preview = _safe_body_preview(body)

    assert "plain-text-password" not in preview
    assert "refresh-secret" not in preview
    assert preview.count("***") == 2


def test_non_json_admin_body_is_not_logged():
    assert _safe_body_preview(b"binary-or-form-data") == "<非 JSON 请求体已省略>"


def test_admin_log_redacts_sensitive_query_values():
    preview = _safe_query_preview("store_id=1&access_token=query-secret")

    assert "store_id=1" in preview
    assert "query-secret" not in preview


def test_production_rejects_default_secret():
    with pytest.raises(ValidationError):
        Settings(
            environment="production",
            auto_seed_demo=False,
            jwt_secret_key="change-this-in-production",
        )


def test_production_accepts_secure_configuration():
    settings = Settings(
        environment="production",
        auto_seed_demo=False,
        jwt_secret_key="a-secure-production-secret-with-32-characters",
    )
    assert settings.environment == "production"
