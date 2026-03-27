from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.seat import create_seat, delete_seat, get_seat, list_seats, update_seat
from app.crud.store import get_store
from app.db.session import get_db
from app.deps import require_admin
from app.schemas.seat import SeatCreate, SeatOut, SeatUpdate

router = APIRouter()


@router.post("/", response_model=SeatOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_seat_api(payload: SeatCreate, db: Session = Depends(get_db)) -> SeatOut:
    if get_store(db, payload.store_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="store not found")
    try:
        return create_seat(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc.orig)) from exc


@router.get("/", response_model=list[SeatOut])
def list_seats_api(
    skip: int = 0,
    limit: int = 100,
    store_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[SeatOut]:
    return list_seats(db, skip=skip, limit=limit, store_id=store_id)


@router.get("/{seat_id}", response_model=SeatOut)
def get_seat_api(seat_id: int, db: Session = Depends(get_db)) -> SeatOut:
    seat = get_seat(db, seat_id)
    if seat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="seat not found")
    return seat


@router.put("/{seat_id}", response_model=SeatOut, dependencies=[Depends(require_admin)])
def update_seat_api(seat_id: int, payload: SeatUpdate, db: Session = Depends(get_db)) -> SeatOut:
    seat = get_seat(db, seat_id)
    if seat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="seat not found")
    if payload.store_id is not None and get_store(db, payload.store_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="store not found")
    try:
        return update_seat(db, seat, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc.orig)) from exc


@router.delete("/{seat_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_seat_api(seat_id: int, db: Session = Depends(get_db)) -> Response:
    seat = get_seat(db, seat_id)
    if seat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="seat not found")
    delete_seat(db, seat)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
