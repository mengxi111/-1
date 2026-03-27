from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.store import create_store, delete_store, get_store, list_stores, update_store
from app.db.session import get_db
from app.deps import require_admin
from app.schemas.store import StoreCreate, StoreOut, StoreUpdate

router = APIRouter()


@router.post("/", response_model=StoreOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_store_api(payload: StoreCreate, db: Session = Depends(get_db)) -> StoreOut:
    try:
        return create_store(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc.orig)) from exc


@router.get("/", response_model=list[StoreOut])
def list_stores_api(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[StoreOut]:
    return list_stores(db, skip=skip, limit=limit)


@router.get("/{store_id}", response_model=StoreOut)
def get_store_api(store_id: int, db: Session = Depends(get_db)) -> StoreOut:
    store = get_store(db, store_id)
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="store not found")
    return store


@router.put("/{store_id}", response_model=StoreOut, dependencies=[Depends(require_admin)])
def update_store_api(store_id: int, payload: StoreUpdate, db: Session = Depends(get_db)) -> StoreOut:
    store = get_store(db, store_id)
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="store not found")
    try:
        return update_store(db, store, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc.orig)) from exc


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_store_api(store_id: int, db: Session = Depends(get_db)) -> Response:
    store = get_store(db, store_id)
    if store is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="store not found")
    delete_store(db, store)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
