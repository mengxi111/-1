from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.crud.user import get_user_by_phone
from app.db.session import get_db
from app.deps import CurrentAuthUser, require_login_token_user
from app.models.user import User
from app.schemas.auth import AuthUserOut, LoginRequest, RegisterRequest, TokenResponse

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_api(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    exists = get_user_by_phone(db, payload.phone)
    if exists is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="phone already registered")

    user = User(
        phone=payload.phone,
        name=payload.name,
        role="student",
        status=1,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id), user.role)
    return TokenResponse(
        access_token=token,
        user=AuthUserOut(id=user.id, phone=user.phone, email=user.email, name=user.name, role=user.role),
    )


@router.post("/login", response_model=TokenResponse)
def login_api(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = get_user_by_phone(db, payload.phone)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="phone or password invalid")
    if user.status != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user disabled")

    token = create_access_token(str(user.id), user.role)
    return TokenResponse(
        access_token=token,
        user=AuthUserOut(id=user.id, phone=user.phone, email=user.email, name=user.name, role=user.role),
    )


@router.get("/me", response_model=AuthUserOut)
def me_api(user: CurrentAuthUser = Depends(require_login_token_user)) -> AuthUserOut:
    return AuthUserOut(id=user.id, phone=user.phone, email=user.email, name=user.name, role=user.role)
