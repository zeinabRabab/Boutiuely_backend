"""
Monitoring Service
==================
Lightweight request/activity logging system.
All logs are stored in the database and exposed via /system-report.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from models.monitoring import APILog, ActivityLog
from schemas import SystemReport


def log_api_request(
    db: Session,
    endpoint: str,
    method: str,
    status_code: int,
    duration_ms: float,
    ip_address: str = "unknown",
) -> None:
    """Called by the middleware on every request."""
    # Skip logging the logs endpoint to avoid infinite recursion noise
    if "/system-report" in endpoint or "/docs" in endpoint or "/redoc" in endpoint:
        return

    log = APILog(
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        duration_ms=duration_ms,
        ip_address=ip_address,
        is_error=status_code >= 400,
    )
    db.add(log)
    db.commit()


def log_activity(db: Session, action: str, user_id: int = None, details: str = None, ip: str = None):
    """Log a user action (login, purchase, etc.)."""
    log = ActivityLog(user_id=user_id, action=action, details=details, ip_address=ip)
    db.add(log)
    db.commit()


def get_system_report(db: Session) -> SystemReport:
    """Aggregate monitoring data into a system health report."""
    total_api = db.query(APILog).count()
    error_count = db.query(APILog).filter(APILog.is_error == True).count()
    avg_ms = db.query(func.avg(APILog.duration_ms)).scalar() or 0.0

    error_rate = (error_count / total_api * 100) if total_api > 0 else 0.0

    # Top 10 most-called endpoints
    top_endpoints = (
        db.query(APILog.endpoint, func.count(APILog.id).label("calls"))
        .group_by(APILog.endpoint)
        .order_by(func.count(APILog.id).desc())
        .limit(10)
        .all()
    )

    # Recent errors
    recent_errors = (
        db.query(APILog)
        .filter(APILog.is_error == True)
        .order_by(APILog.created_at.desc())
        .limit(10)
        .all()
    )

    # Login attempts in last 24h
    since_24h = datetime.utcnow() - timedelta(hours=24)
    login_attempts = (
        db.query(ActivityLog)
        .filter(ActivityLog.action == "login", ActivityLog.created_at >= since_24h)
        .count()
    )

    # Recommendation requests
    rec_requests = (
        db.query(APILog)
        .filter(APILog.endpoint.contains("/recommendations"))
        .count()
    )

    return SystemReport(
        total_api_calls=total_api,
        error_rate_percent=round(error_rate, 2),
        avg_response_ms=round(avg_ms, 2),
        top_endpoints=[{"endpoint": r.endpoint, "calls": r.calls} for r in top_endpoints],
        recent_errors=[
            {
                "endpoint": e.endpoint,
                "status": e.status_code,
                "time": e.created_at.isoformat() if e.created_at else "",
            }
            for e in recent_errors
        ],
        login_attempts_24h=login_attempts,
        recommendation_requests=rec_requests,
    )
