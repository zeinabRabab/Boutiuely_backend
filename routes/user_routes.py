from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import UserResponse, UserRegister
from backend.auth import require_admin, get_current_user, hash_password
from backend.models.user import User
from backend.services import get_all_users, get_user_by_id, delete_user
from fastapi import HTTPException

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.get("/", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin only — list all users."""
    return get_all_users(db)


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(
    payload: UserRegister,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin only — create a new user directly (no login token returned)."""
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    allowed_roles = ("admin", "cashier", "manager", "viewer")
    role = payload.role if payload.role in allowed_roles else "cashier"
    user = User(
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin only — get a specific user by ID."""
    return get_user_by_id(user_id, db)


@router.delete("/{user_id}")
def remove_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin only — delete a user."""
    return delete_user(user_id, db)
