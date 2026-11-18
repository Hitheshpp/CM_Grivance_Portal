from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..constants import CATEGORIES, DISTRICTS, PRIORITIES, STATUS_RESOLVED, STATUSES, VIS_PUBLIC
from ..database import get_db
from ..models import ContactEnquiry, Department, Grievance
from ..schemas import ContactIn
from ..security import RateLimiter
from ..services.workflow import aware, is_overdue
from ..models import utcnow

router = APIRouter(prefix="/api/public", tags=["Public"])
contact_limit = RateLimiter(5, 300, "contact form")
track_limit = RateLimiter(30, 60, "tracking")


@router.get("/meta")
def meta():
    return {"districts": DISTRICTS, "categories": CATEGORIES, "priorities": PRIORITIES, "statuses": STATUSES}


@router.get("/departments")
def departments(db: Session = Depends(get_db)):
    rows = db.scalars(select(Department).order_by(Department.name)).all()
    return [{"id": d.id, "code": d.code, "name": d.name, "description": d.description,
             "category": d.default_category} for d in rows]


@router.get("/stats")
def public_stats(db: Session = Depends(get_db)):
    """Aggregate, non-personal figures for the home page (computed from stored data)."""
    total = db.scalar(select(func.count(Grievance.id))) or 0
    resolved = db.scalar(select(func.count(Grievance.id)).where(Grievance.status == STATUS_RESOLVED)) or 0
    depts = db.scalar(select(func.count(Department.id))) or 0
    districts = db.scalar(select(func.count(func.distinct(Grievance.district)))) or 0
    return {"total_grievances": total, "resolved": resolved,
            "resolution_rate": round(resolved * 100 / total) if total else 0,
            "departments": depts, "districts_covered": districts}


@router.post("/contact", status_code=201, dependencies=[Depends(contact_limit)])
def contact(body: ContactIn, db: Session = Depends(get_db)):
    db.add(ContactEnquiry(name=body.name.strip(), email=body.email, subject=body.subject.strip(),
                          message=body.message.strip()))
    db.commit()
    return {"message": "Thank you. Your enquiry has been recorded."}


@router.get("/track/{reference_no}", dependencies=[Depends(track_limit)])
def track(reference_no: str, db: Session = Depends(get_db)):
    """Public tracking by reference number: status, department and *public* history only.
    No complaint text, personal data, attachments or internal remarks are exposed."""
    g = db.scalar(select(Grievance).where(Grievance.reference_no == reference_no.strip().upper()))
    if g is None:
        raise HTTPException(404, "No grievance found with this reference number")
    return {
        "reference_no": g.reference_no, "subject": g.subject, "district": g.district, "category": g.category,
        "status": g.status, "priority": g.priority, "department": g.department.name if g.department else None,
        "created_at": g.created_at, "updated_at": g.updated_at, "overdue": is_overdue(g),
        "history": [{"action": h.action, "from_status": h.from_status, "to_status": h.to_status,
                     "remarks": h.remarks, "created_at": h.created_at, "actor_role": h.actor_role}
                    for h in g.history if h.visibility == VIS_PUBLIC],
    }
