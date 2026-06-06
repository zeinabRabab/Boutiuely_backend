from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import get_current_user, require_admin
from backend.models.user import User
from backend.schemas import OrderCreate, OrderStatusUpdate, OrderResponse
from backend.services import create_order, get_my_orders, get_all_orders, update_order_status

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=201)
def place_order(payload: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Authenticated — place a new order."""
    return create_order(payload, current_user, db)


@router.get("/my", response_model=List[OrderResponse])
def my_orders(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Authenticated — get orders for the current user."""
    return get_my_orders(current_user, db, status=status, skip=skip, limit=limit)


@router.get("/", response_model=List[OrderResponse])
def all_orders(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin only — get all orders with optional status filter."""
    return get_all_orders(db, status=status, skip=skip, limit=limit)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def change_status(order_id: int, payload: OrderStatusUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin only — update order status."""
    return update_order_status(order_id, payload, db)
