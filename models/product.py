"""
Product model — extended with AI recommendation fields and stock alert threshold.
"""
from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import relationship
from database.db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    category = Column(String(100), nullable=True, index=True)

    # ── Stock alert ───────────────────────────────────────────────────────────
    alert_threshold = Column(Integer, default=5, nullable=False)

    # ── AI / recommendation fields ────────────────────────────────────────────
    tags = Column(String(500), nullable=True)
    color = Column(String(100), nullable=True)
    image_url = Column(String(500), nullable=True)

    order_items = relationship("OrderItem", back_populates="product")
