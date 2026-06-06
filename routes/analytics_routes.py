from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from auth import require_admin
from models.user import User
from schemas import DashboardStats, AnalysisReport
from services import (
    get_dashboard_stats, get_top_products, get_revenue_trend,
    get_order_status_breakdown, generate_full_analysis,
)
from services.analytics_service import (
    get_category_breakdown, get_user_growth, get_inventory_summary
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin — KPI dashboard statistics."""
    return get_dashboard_stats(db)


@router.get("/top-products")
def top_products(limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin — top-selling products."""
    return get_top_products(db, limit=limit)


@router.get("/revenue-trend")
def revenue_trend(days: int = Query(30, ge=7, le=365), db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin — daily revenue for the past N days."""
    return get_revenue_trend(db, days=days)


@router.get("/order-status")
def order_status(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin — order count per status."""
    return get_order_status_breakdown(db)


@router.get("/category-breakdown")
def category_breakdown(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin — revenue and units sold broken down by product category."""
    return get_category_breakdown(db)


@router.get("/user-growth")
def user_growth(days: int = Query(30, ge=7, le=365), db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin — new users per day for the past N days."""
    return get_user_growth(db, days=days)


@router.get("/inventory")
def inventory_summary(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin — full inventory summary by stock level and category."""
    return get_inventory_summary(db)


@router.get("/analyze", response_model=AnalysisReport)
def analyze_project(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin — run full AI project analysis and return insights + recommendations."""
    return generate_full_analysis(db)
