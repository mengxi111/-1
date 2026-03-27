from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles

from app.api.grouped_router import grouped_api_router
from app.core.api_response import http_exception_handler, validation_exception_handler
from app.core.config import settings
from app.db.session import SessionLocal
from app.middleware.admin_operation_log import AdminOperationLogMiddleware
from app.middleware.api_response_wrapper import ApiResponseWrapperMiddleware
from app.services.demo_seed import bootstrap_demo_data
from app.tasks.scheduler import scheduler
from app.ui.router import router as ui_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    db = SessionLocal()
    try:
        bootstrap_result = bootstrap_demo_data(db=db, only_if_empty=True)
        if bootstrap_result.total_created > 0:
            logger.info(
                (
                    "初始化完成: stores=%s, areas=%s, seats=%s, plans=%s, "
                    "users=%s, bookings=%s, orders=%s, notices=%s, notifications=%s"
                ),
                bootstrap_result.stores_created,
                bootstrap_result.areas_created,
                bootstrap_result.seats_created,
                bootstrap_result.plans_created,
                bootstrap_result.users_created,
                bootstrap_result.bookings_created,
                bootstrap_result.orders_created,
                bootstrap_result.notices_created,
                bootstrap_result.notifications_created,
            )
    except Exception:
        logger.exception("启动时初始化种子数据失败")
    finally:
        db.close()

    if not scheduler.running:
        scheduler.start()
    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(AdminOperationLogMiddleware)
app.add_middleware(ApiResponseWrapperMiddleware)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.include_router(grouped_api_router, prefix="/api")
app.include_router(ui_router)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/healthz", tags=["health"])
def healthz() -> dict[str, str]:
    return {"status": "ok"}
