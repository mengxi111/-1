from fastapi import APIRouter, Depends, HTTPException, status
from redis import Redis
from sqlalchemy.orm import Session

from app.crud.booking import (
    BookingConflictError,
    BookingNotFoundError,
    BookingValidationError,
    BookingStateError,
    LockServiceUnavailableError,
    SeatLockBusyError,
    SeatNotFoundError,
    SeatUnavailableError,
    StoreBusinessHourError,
    UserBlacklistedError,
    UserNotFoundError,
    VerificationCodeError,
    checkin_booking,
    create_booking_with_lock,
    get_booking,
    list_bookings,
)
from app.db.session import get_db
from app.deps import CurrentAuthUser, get_redis_client, require_login_token_user
from app.schemas.booking import (
    BookingCheckinRequest,
    BookingCheckinResponse,
    BookingCreate,
    BookingCreateResponse,
    BookingOut,
)

router = APIRouter()


@router.post("/", response_model=BookingCreateResponse, status_code=status.HTTP_201_CREATED)
def create_booking_api(
    payload: BookingCreate,
    db: Session = Depends(get_db),
    lock_client: Redis = Depends(get_redis_client),
    current_user: CurrentAuthUser = Depends(require_login_token_user),
) -> BookingCreateResponse:
    if current_user.role in {"admin", "super_admin"}:
        if payload.user_id is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="admin must provide user_id")
        effective_user_id = payload.user_id
    else:
        if payload.user_id is not None and payload.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="cannot create booking for another user")
        effective_user_id = current_user.id

    try:
        booking = create_booking_with_lock(
            db,
            lock_client,
            BookingCreate(
                seat_id=payload.seat_id,
                start_time=payload.start_time,
                end_time=payload.end_time,
                user_id=effective_user_id,
            ),
        )
        return BookingCreateResponse(booking_id=booking.id, status=booking.status)
    except SeatNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookingValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except SeatUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该座位当前不可用，请选择其他座位") from exc
    except StoreBusinessHourError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="所选时间不在门店营业时间内") from exc
    except UserBlacklistedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="黑名单用户禁止预约") from exc
    except SeatLockBusyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "SEAT_LOCK_BUSY", "message": str(exc)},
        ) from exc
    except LockServiceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "LOCK_SERVICE_UNAVAILABLE", "message": str(exc)},
        ) from exc
    except BookingConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "BOOKING_TIME_CONFLICT", "message": str(exc)},
        ) from exc
    except BookingStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/", response_model=list[BookingOut])
def list_bookings_api(
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_login_token_user),
) -> list[BookingOut]:
    if user_id is not None and current_user.role not in {"admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin role required for user_id filter")

    if user_id is None and current_user.role not in {"admin", "super_admin"}:
        return list_bookings(db, skip=skip, limit=limit, user_id=current_user.id)
    return list_bookings(db, skip=skip, limit=limit, user_id=user_id)


@router.get("/me", response_model=list[BookingOut])
def list_my_bookings_api(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_login_token_user),
) -> list[BookingOut]:
    return list_bookings(db, skip=skip, limit=limit, user_id=current_user.id)


@router.get("/{booking_id}", response_model=BookingOut)
def get_booking_api(booking_id: int, db: Session = Depends(get_db)) -> BookingOut:
    booking = get_booking(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="booking not found")
    return booking


@router.post("/{booking_id}/checkin", response_model=BookingCheckinResponse)
def checkin_booking_api(
    booking_id: int,
    payload: BookingCheckinRequest | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentAuthUser = Depends(require_login_token_user),
) -> BookingCheckinResponse:
    booking = get_booking(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="booking not found")
    if current_user.role not in {"admin", "super_admin"} and booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="cannot check in for another user")

    try:
        booking, action, code = checkin_booking(db, booking_id, payload or BookingCheckinRequest())
    except BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BookingStateError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except VerificationCodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UserBlacklistedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="黑名单用户禁止签到") from exc

    if action == "code_generated":
        return BookingCheckinResponse(
            booking_id=booking.id,
            status=booking.status,
            message="verification_code_generated",
            verification_code=code,
        )
    if action == "checked_in":
        return BookingCheckinResponse(
            booking_id=booking.id,
            status=booking.status,
            message="checkin_success",
        )
    return BookingCheckinResponse(
        booking_id=booking.id,
        status=booking.status,
        message="already_checked_in",
    )
