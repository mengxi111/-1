from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.user import create_user, delete_user, get_user, list_users, update_user
from app.db.session import get_db
from app.deps import require_admin
from app.schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter()


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_user_api(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    try:
        return create_user(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc.orig)) from exc


@router.get("/", response_model=list[UserOut], dependencies=[Depends(require_admin)])
def list_users_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[UserOut]:
    return list_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)])
def get_user_api(user_id: int, db: Session = Depends(get_db)) -> UserOut:
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return user


@router.put("/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)])
def update_user_api(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> UserOut:
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    try:
        return update_user(db, user, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc.orig)) from exc


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_user_api(user_id: int, db: Session = Depends(get_db)) -> Response:
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    delete_user(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
