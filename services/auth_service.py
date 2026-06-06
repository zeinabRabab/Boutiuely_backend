from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.schemas import UserRegister, UserLogin, TokenResponse
from backend.auth import hash_password, verify_password, create_access_token


def register_user(payload: UserRegister, db: Session) -> TokenResponse:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        role=payload.role if payload.role in ("admin", "cashier") else "cashier",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user_id=user.id, name=user.name, role=user.role)


def login_user(payload: UserLogin, db: Session) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user_id=user.id, name=user.name, role=user.role)
