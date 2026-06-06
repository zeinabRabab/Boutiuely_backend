from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth import require_admin
from backend.models.user import User
from backend.schemas import SystemReport
from backend.services import get_system_report

router = APIRouter(prefix="/system-report", tags=["Monitoring"])


@router.get("/", response_model=SystemReport)
def system_report(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Admin — system health report: API stats, error rates, monitoring data."""
    return get_system_report(db)
