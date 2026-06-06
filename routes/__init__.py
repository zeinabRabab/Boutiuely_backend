from .auth_routes import router as auth_router
from .user_routes import router as user_router
from .product_routes import router as product_router
from .order_routes import router as order_router
from .analytics_routes import router as analytics_router
from .recommendation_routes import router as recommendation_router
from .report_routes import router as report_router
from .monitoring_routes import router as monitoring_router

__all__ = [
    "auth_router",
    "user_router",
    "product_router",
    "order_router",
    "analytics_router",
    "recommendation_router",
    "report_router",
    "monitoring_router",
]
