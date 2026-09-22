from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.member_card import (
    create_member_card,
    delete_member_card,
    get_member_card,
    list_member_cards,
    update_member_card,
)
from app.crud.user import get_user
from app.db.session import get_db
from app.deps import require_admin
from app.schemas.member_card import MemberCardCreate, MemberCardOut, MemberCardUpdate

router = APIRouter()


@router.post("/", response_model=MemberCardOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_member_card_api(payload: MemberCardCreate, db: Session = Depends(get_db)) -> MemberCardOut:
    if get_user(db, payload.user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    try:
        return create_member_card(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc.orig)) from exc


@router.get("/", response_model=list[MemberCardOut], dependencies=[Depends(require_admin)])
def list_member_cards_api(
    skip: int = 0,
    limit: int = 100,
    user_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[MemberCardOut]:
    return list_member_cards(db, skip=skip, limit=limit, user_id=user_id)


@router.get("/{card_id}", response_model=MemberCardOut, dependencies=[Depends(require_admin)])
def get_member_card_api(card_id: int, db: Session = Depends(get_db)) -> MemberCardOut:
    card = get_member_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="member card not found")
    return card


@router.put("/{card_id}", response_model=MemberCardOut, dependencies=[Depends(require_admin)])
def update_member_card_api(card_id: int, payload: MemberCardUpdate, db: Session = Depends(get_db)) -> MemberCardOut:
    card = get_member_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="member card not found")
    if payload.user_id is not None and get_user(db, payload.user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    try:
        return update_member_card(db, card, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc.orig)) from exc


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_member_card_api(card_id: int, db: Session = Depends(get_db)) -> Response:
    card = get_member_card(db, card_id)
    if card is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="member card not found")
    delete_member_card(db, card)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
