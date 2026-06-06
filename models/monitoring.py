"""
Monitoring models:
  ActivityLog  — tracks user actions (login, purchase, view)
  APILog       — tracks API requests with status codes and duration
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database.db import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # null = anonymous
    action = Column(String(100), nullable=False)      # e.g. "login", "view_product", "order"
    details = Column(String(500), nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="activity_logs")


class APILog(Base):
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(300), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    duration_ms = Column(Float, nullable=True)
    ip_address = Column(String(50), nullable=True)
    is_error = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
