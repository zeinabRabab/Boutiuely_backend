from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.models.user import User
from backend.schemas import UserResponse


def get_all_users(db: Session) -> List[UserResponse]:
    return [UserResponse.model_validate(u) for u in db.query(User).order_by(User.created_at.desc()).all()]


def get_user_by_id(user_id: int, db: Session) -> UserResponse:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


def delete_user(user_id: int, db: Session) -> dict:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin users")
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted successfully"}
