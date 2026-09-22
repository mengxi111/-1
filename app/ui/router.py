from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse, Response

from app.core.config import settings

router = APIRouter(include_in_schema=False)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
STUDENT_FILE = STATIC_DIR / "student.html"
STUDENT_NOTICES_FILE = STATIC_DIR / "student_notices.html"
STUDENT_NOTIFICATIONS_FILE = STATIC_DIR / "student_notifications.html"
AUTH_FILE = STATIC_DIR / "auth.html"
ADMIN_DIR = STATIC_DIR / "admin"

ADMIN_PAGES = {
    "dashboard": ADMIN_DIR / "dashboard.html",
    "stores": ADMIN_DIR / "stores.html",
    "resources": ADMIN_DIR / "resources.html",
    "orders": ADMIN_DIR / "orders.html",
    "users": ADMIN_DIR / "users.html",
    "notices": ADMIN_DIR / "notices.html",
    "config": ADMIN_DIR / "config.html",
    "logs": ADMIN_DIR / "logs.html",
}


def _admin_page(name: str) -> FileResponse:
    page = ADMIN_PAGES.get(name)
    if page is None:
        return FileResponse(ADMIN_PAGES["dashboard"])
    return FileResponse(page)


@router.get("/")
def root_redirect() -> RedirectResponse:
    return RedirectResponse(url="/auth/login", status_code=307)


@router.get("/auth")
def auth_redirect() -> RedirectResponse:
    return RedirectResponse(url="/auth/login", status_code=307)


@router.get("/auth/login")
def auth_login_ui() -> FileResponse:
    return FileResponse(AUTH_FILE)


@router.get("/auth/register")
def auth_register_ui() -> FileResponse:
    return FileResponse(AUTH_FILE)


@router.get("/student")
def student_ui() -> FileResponse:
    return FileResponse(STUDENT_FILE)


@router.get("/student/checkin")
def student_checkin_ui() -> FileResponse:
    return FileResponse(STUDENT_FILE)


@router.get("/student/notices")
def student_notices_ui() -> FileResponse:
    return FileResponse(STUDENT_NOTICES_FILE)


@router.get("/student/notifications")
def student_notifications_ui() -> FileResponse:
    return FileResponse(STUDENT_NOTIFICATIONS_FILE)


@router.get("/admin")
def admin_root() -> RedirectResponse:
    return RedirectResponse(url="/admin/dashboard", status_code=307)


@router.get("/admin/dashboard")
def admin_dashboard_ui() -> FileResponse:
    return _admin_page("dashboard")


@router.get("/admin/stores")
def admin_stores_ui() -> FileResponse:
    return _admin_page("stores")


@router.get("/admin/resources")
def admin_resources_ui() -> FileResponse:
    return _admin_page("resources")


@router.get("/admin/orders")
def admin_orders_ui() -> Response:
    if not settings.order_module_enabled:
        return RedirectResponse(url="/admin/dashboard", status_code=307)
    return _admin_page("orders")


@router.get("/admin/users")
def admin_users_ui() -> FileResponse:
    return _admin_page("users")


@router.get("/admin/notices")
def admin_notices_ui() -> FileResponse:
    return _admin_page("notices")


@router.get("/admin/config")
def admin_config_ui() -> FileResponse:
    return _admin_page("config")


@router.get("/admin/logs")
def admin_logs_ui() -> FileResponse:
    return _admin_page("logs")


@router.get("/ui")
def legacy_admin_ui_redirect() -> RedirectResponse:
    return RedirectResponse(url="/admin/dashboard", status_code=307)


@router.get("/auth-ui")
def legacy_auth_ui_redirect() -> RedirectResponse:
    return RedirectResponse(url="/auth/login", status_code=307)
