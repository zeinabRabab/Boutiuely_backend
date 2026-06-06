from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from backend.models.order import Order, OrderItem, OrderStatus
from backend.models.product import Product
from backend.models.user import User
from backend.schemas import OrderCreate, OrderStatusUpdate, OrderResponse


def create_order(payload: OrderCreate, current_user: User, db: Session) -> OrderResponse:
    total_price = 0.0
    resolved = []

    for item_input in payload.items:
        product = db.query(Product).filter(Product.id == item_input.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_input.product_id} not found")
        if product.stock < item_input.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{product.name}'. Available: {product.stock}",
            )
        resolved.append((product, item_input.quantity))
        total_price += product.price * item_input.quantity

    order = Order(user_id=current_user.id, total_price=round(total_price, 2), status=OrderStatus.pending)
    db.add(order)
    db.flush()

    for product, quantity in resolved:
        db.add(OrderItem(order_id=order.id, product_id=product.id, quantity=quantity, unit_price=product.price))
        product.stock -= quantity

    db.commit()
    db.refresh(order)
    return _load_full_order(order.id, db)


def get_my_orders(
    current_user: User,
    db: Session,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[OrderResponse]:
    query = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.user_id == current_user.id)
    )
    if status:
        query = query.filter(Order.status == status)
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return [OrderResponse.model_validate(o) for o in orders]


def get_all_orders(
    db: Session,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[OrderResponse]:
    query = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
    )
    if status:
        query = query.filter(Order.status == status)
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return [OrderResponse.model_validate(o) for o in orders]


def update_order_status(order_id: int, payload: OrderStatusUpdate, db: Session) -> OrderResponse:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    try:
        order.status = OrderStatus(payload.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")
    db.commit()
    return _load_full_order(order_id, db)


def _load_full_order(order_id: int, db: Session) -> OrderResponse:
    order = (
        db.query(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order_id)
        .first()
    )
    return OrderResponse.model_validate(order)
