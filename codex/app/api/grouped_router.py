from fastapi import APIRouter

from app.api import admin, auth, student

grouped_api_router = APIRouter()
grouped_api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
grouped_api_router.include_router(student.router, prefix="/student", tags=["student"])
grouped_api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

