"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════
# AUTH / USER SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[str] = "cashier"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ("admin", "cashier", "manager", "viewer", None):
            raise ValueError("Role must be 'admin' or 'cashier'")
        return v if v else "cashier"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    role: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════
# PRODUCT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0
    category: Optional[str] = None
    tags: Optional[str] = None
    color: Optional[str] = None
    image_url: Optional[str] = None
    alert_threshold: int = 5

    @field_validator("price")
    @classmethod
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError("Price must be positive")
        return v

    @field_validator("stock")
    @classmethod
    def stock_non_negative(cls, v):
        if v < 0:
            raise ValueError("Stock cannot be negative")
        return v

    @field_validator("alert_threshold")
    @classmethod
    def threshold_non_negative(cls, v):
        if v < 0:
            raise ValueError("Alert threshold cannot be negative")
        return v


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    color: Optional[str] = None
    image_url: Optional[str] = None
    alert_threshold: Optional[int] = None


class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    stock: int
    category: Optional[str]
    tags: Optional[str]
    color: Optional[str]
    image_url: Optional[str]
    alert_threshold: int = 5
    model_config = {"from_attributes": True}


class LowStockProduct(BaseModel):
    id: int
    name: str
    category: Optional[str]
    stock: int
    alert_threshold: int
    status: str  # "critical" | "low" | "out"
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════
# ORDER SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class OrderItemInput(BaseModel):
    product_id: int
    quantity: int

    @field_validator("quantity")
    @classmethod
    def qty_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v


class OrderCreate(BaseModel):
    items: List[OrderItemInput]


class OrderStatusUpdate(BaseModel):
    status: str


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    product: Optional[ProductResponse] = None
    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_price: float
    status: str
    created_at: Optional[datetime] = None
    items: List[OrderItemResponse] = []
    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════════════════
# ANALYTICS SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class DashboardStats(BaseModel):
    total_products: int
    total_orders: int
    total_users: int
    total_revenue: float
    pending_orders: int
    delivered_orders: int
    low_stock_count: int


class TopProduct(BaseModel):
    product_id: int
    name: str
    category: Optional[str]
    total_sold: int
    total_revenue: float


class RevenuePoint(BaseModel):
    date: str
    revenue: float
    orders: int


class OrderStatusCount(BaseModel):
    status: str
    count: int


class AnalysisReport(BaseModel):
    generated_at: str
    summary: dict
    top_products: List[TopProduct]
    revenue_trend: List[RevenuePoint]
    order_status_breakdown: List[OrderStatusCount]
    insights: List[str]
    recommendations: List[str]


# ═══════════════════════════════════════════════════════════════════════
# MONITORING SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class SystemReport(BaseModel):
    total_api_calls: int
    error_rate_percent: float
    avg_response_ms: float
    top_endpoints: List[dict]
    recent_errors: List[dict]
    login_attempts_24h: int
    recommendation_requests: int


# ═══════════════════════════════════════════════════════════════════════
# BULK IMPORT SCHEMAS
# ═══════════════════════════════════════════════════════════════════════

class BulkImportRow(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0
    category: Optional[str] = None
    color: Optional[str] = None
    tags: Optional[str] = None
    image_url: Optional[str] = None
    alert_threshold: int = 5
    row_index: int
    errors: List[str] = []
    is_valid: bool = True


class BulkImportResult(BaseModel):
    total: int
    valid: int
    invalid: int
    imported: int
    rows: List[BulkImportRow]
    errors: List[str] = []
