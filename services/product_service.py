from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.models.product import Product
from backend.models.order import OrderItem
from backend.schemas import ProductCreate, ProductUpdate, ProductResponse


def create_product(payload: ProductCreate, db: Session) -> ProductResponse:
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return ProductResponse.model_validate(product)


def get_all_products(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[ProductResponse]:
    query = db.query(Product)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category:
        query = query.filter(Product.category == category)
    return [ProductResponse.model_validate(p) for p in query.offset(skip).limit(limit).all()]


def get_product_by_id(product_id: int, db: Session) -> ProductResponse:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(product)


def update_product(product_id: int, payload: ProductUpdate, db: Session) -> ProductResponse:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return ProductResponse.model_validate(product)


def delete_product(product_id: int, db: Session) -> dict:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    linked = db.query(OrderItem).filter(OrderItem.product_id == product_id).first()
    if linked:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete product referenced in orders. Set stock to 0 to hide it.",
        )
    db.delete(product)
    db.commit()
    return {"message": f"Product {product_id} deleted"}
