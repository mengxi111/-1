from fastapi import APIRouter

from app.api.v1 import auth, booking, member_card, seat, stats, store, user

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(store.router, prefix="/stores", tags=["stores"])
api_router.include_router(seat.router, prefix="/seats", tags=["seats"])
api_router.include_router(user.router, prefix="/users", tags=["users"])
api_router.include_router(member_card.router, prefix="/member-cards", tags=["member-cards"])
api_router.include_router(booking.router, prefix="/bookings", tags=["bookings"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
