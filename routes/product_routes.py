from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import csv, io

from database import get_db
from auth import require_admin, get_current_user
from models.user import User
from models.product import Product
from schemas import (
    ProductCreate, ProductUpdate, ProductResponse,
    LowStockProduct, BulkImportResult, BulkImportRow,
)
from services import (
    create_product, get_all_products, get_product_by_id, update_product, delete_product,
)

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, status_code=201)
def add_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return create_product(payload, db)


# ─── IMPORTANT: static routes before /{product_id} ───────────────────────────

@router.get("/low-stock", response_model=List[LowStockProduct])
def get_low_stock(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Return products at or below their alert threshold."""
    products = (
        db.query(Product)
        .filter(Product.stock <= Product.alert_threshold)
        .order_by(Product.stock.asc())
        .all()
    )
    result = []
    for p in products:
        if p.stock == 0:
            status = "out"
        elif p.stock <= max(p.alert_threshold // 2, 1):
            status = "critical"
        else:
            status = "low"
        result.append(
            LowStockProduct(
                id=p.id,
                name=p.name,
                category=p.category,
                stock=p.stock,
                alert_threshold=p.alert_threshold,
                status=status,
            )
        )
    return result


@router.post("/bulk-import", response_model=BulkImportResult)
async def bulk_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Parse CSV or XLSX and bulk-insert valid products."""
    content = await file.read()
    filename = (file.filename or "").lower()
    raw_rows: List[dict] = []

    if filename.endswith(".csv"):
        try:
            text = content.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text))
            raw_rows = [dict(r) for r in reader]
        except Exception as e:
            raise HTTPException(400, f"Failed to parse CSV: {e}")

    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
            ws = wb.active
            headers = None
            for row in ws.iter_rows(values_only=True):
                if headers is None:
                    headers = [str(c).strip() if c is not None else "" for c in row]
                else:
                    raw_rows.append(
                        {h: (str(v).strip() if v is not None else "") for h, v in zip(headers, row)}
                    )
        except ImportError:
            raise HTTPException(503, "openpyxl not installed — run: pip install openpyxl")
        except Exception as e:
            raise HTTPException(400, f"Failed to parse Excel file: {e}")
    else:
        raise HTTPException(400, "Only .csv and .xlsx files are supported.")

    if not raw_rows:
        raise HTTPException(400, "File is empty or has no data rows.")

    # Validate required columns
    if raw_rows:
        cols = {c.strip().lower() for c in raw_rows[0].keys()}
        # Accept "name" or "product name"
        has_name = "name" in cols or "product name" in cols
        has_price = "price" in cols
        if not has_name or not has_price:
            missing = []
            if not has_name:
                missing.append("Name")
            if not has_price:
                missing.append("Price")
            raise HTTPException(400, f"Missing required columns: {', '.join(missing)}")

    rows: List[BulkImportRow] = []

    for i, raw in enumerate(raw_rows):
        row_data = {k.strip().lower(): (v.strip() if isinstance(v, str) else str(v) if v is not None else "") for k, v in raw.items()}
        errors = []

        name = row_data.get("name") or row_data.get("product name") or ""
        if not name or name.lower() == "none":
            errors.append("Missing product name")
            name = ""

        try:
            price = float(row_data.get("price", "0") or "0")
            if price <= 0:
                errors.append("Price must be positive")
        except (ValueError, TypeError):
            price = 0.0
            errors.append("Invalid price value")

        try:
            stock = int(float(row_data.get("stock", "0") or "0"))
            if stock < 0:
                errors.append("Stock cannot be negative")
        except (ValueError, TypeError):
            stock = 0
            errors.append("Invalid stock value")

        try:
            threshold_raw = row_data.get("alert threshold") or row_data.get("alert_threshold") or "5"
            threshold = int(float(threshold_raw or "5"))
            if threshold < 0:
                threshold = 5
        except (ValueError, TypeError):
            threshold = 5

        row = BulkImportRow(
            name=name,
            price=price,
            stock=stock,
            description=row_data.get("description") or None,
            category=row_data.get("category") or None,
            color=row_data.get("color") or None,
            tags=row_data.get("tags") or None,
            image_url=row_data.get("image url") or row_data.get("image_url") or None,
            alert_threshold=threshold,
            row_index=i + 2,
            errors=errors,
            is_valid=len(errors) == 0 and bool(name),
        )
        rows.append(row)

    imported = 0
    for row in rows:
        if not row.is_valid or not row.name:
            continue
        existing = db.query(Product).filter(Product.name == row.name).first()
        if existing:
            row.errors.append(f"Duplicate: '{row.name}' already exists")
            row.is_valid = False
            continue
        p = Product(
            name=row.name,
            description=row.description,
            price=row.price,
            stock=row.stock,
            category=row.category,
            color=row.color,
            tags=row.tags,
            image_url=row.image_url,
            alert_threshold=row.alert_threshold,
        )
        db.add(p)
        imported += 1

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Database error during import: {e}")

    valid = sum(1 for r in rows if r.is_valid)
    invalid = len(rows) - valid

    return BulkImportResult(
        total=len(rows),
        valid=valid,
        invalid=invalid,
        imported=imported,
        rows=rows,
    )


@router.get("/", response_model=List[ProductResponse])
def list_products(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return get_all_products(db, search=search, category=category, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return get_product_by_id(product_id, db)


@router.put("/{product_id}", response_model=ProductResponse)
def edit_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return update_product(product_id, payload, db)


@router.delete("/{product_id}")
def remove_product(
    product_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return delete_product(product_id, db)
