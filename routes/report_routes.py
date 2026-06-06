from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db
from auth import require_admin
from models.user import User
from services import generate_csv_report, generate_pdf_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/download/csv")
def download_csv(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin — download business report as CSV."""
    content, filename = generate_csv_report(db)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/download/pdf")
def download_pdf(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin — download business report as PDF."""
    try:
        content, filename = generate_pdf_report(db)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ImportError as e:
        return Response(
            content=str(e),
            media_type="text/plain",
            status_code=503,
        )
