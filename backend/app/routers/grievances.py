from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from ..constants import (CATEGORIES, DISTRICTS, PRIORITIES, ROLE_CITIZEN, ROLE_CMO, ROLE_OFFICER, STATUS_RESOLVED,
                         STATUS_SUBMITTED, STATUSES, VIS_PUBLIC)
from ..database import get_db
from ..deps import get_current_user, require_roles
from ..models import Attachment, Feedback, Grievance, User, utcnow
from ..schemas import FeedbackIn, RemarkIn, StatusIn
from ..security import RateLimiter
from ..services import ai_service, files
from ..services.workflow import (add_history, allowed_visibilities, aware, change_status, due_date_for,
                                 get_grievance_or_404, grievance_detail, grievance_summary)

router = APIRouter(prefix="/api/grievances", tags=["Grievances"])
submit_limit = RateLimiter(10, 300, "grievance submission")


@router.post("", status_code=201, dependencies=[Depends(submit_limit)])
def submit_grievance(
    district: str = Form(...), category: str = Form(...), subject: str = Form(..., min_length=5, max_length=200),
    description: str = Form(..., min_length=20, max_length=5000), priority: str | None = Form(None),
    file: UploadFile | None = File(None), user: User = Depends(require_roles(ROLE_CITIZEN)),
    db: Session = Depends(get_db),
):
    """Citizen submits a grievance. `category`/`priority` are the citizen's reviewed choices (typically
    pre-filled from the AI suggestion); the AI analysis itself is stored separately for the CMO."""
    if district not in DISTRICTS:
        raise HTTPException(422, "Unknown district")
    if category not in CATEGORIES:
        raise HTTPException(422, "Unknown category")
    if priority and priority not in PRIORITIES:
        raise HTTPException(422, "Priority must be Low, Medium or High")

    ai = ai_service.analyze(db, description, subject, district)  # cached if the form already called it
    final_priority = priority or ai["priority"]

    g = Grievance(citizen_id=user.id, district=district, category=category, subject=subject.strip(),
                  description=description.strip(), priority=final_priority, status=STATUS_SUBMITTED,
                  due_date=due_date_for(final_priority),
                  ai_department_id=ai["department_id"], ai_category=ai["category"], ai_priority=ai["priority"],
                  ai_summary=ai["summary"], ai_provider=ai["provider"], ai_is_fallback=ai["is_fallback"],
                  ai_duplicates=ai["duplicates"])
    if file is not None and file.filename:
        files.attach(g, file, user, "complaint")  # validates before anything is committed
    db.add(g)
    db.flush()
    year = (aware(g.created_at) or utcnow()).year
    g.reference_no = f"KGR-{year}-{g.id:06d}"
    add_history(db, g, user, "Grievance submitted", STATUS_SUBMITTED, "Grievance registered by citizen",
                from_status=None)
    db.commit()
    return {"reference_no": g.reference_no, "status": g.status, "due_date": g.due_date,
            "message": "Grievance submitted successfully. Keep your reference number to track progress."}


@router.get("")
def list_grievances(
    status: str | None = None, district: str | None = None, category: str | None = None,
    priority: str | None = None, department_id: int | None = None, overdue: bool | None = None,
    escalated: bool | None = None, report_status: str | None = None, q: str | None = Query(None, max_length=100),
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    """Role-scoped list: citizens see their own, officers see their department's, CMO sees all."""
    conds = []
    if user.role == ROLE_CITIZEN:
        conds.append(Grievance.citizen_id == user.id)
    elif user.role == ROLE_OFFICER:
        conds.append(Grievance.department_id == user.department_id)
    if status:
        if status not in STATUSES:
            raise HTTPException(422, "Unknown status")
        conds.append(Grievance.status == status)
    if district:
        conds.append(Grievance.district == district)
    if category:
        conds.append(Grievance.category == category)
    if priority:
        conds.append(Grievance.priority == priority)
    if department_id and user.role == ROLE_CMO:
        conds.append(Grievance.department_id == department_id)
    if overdue is not None:
        is_od = and_(Grievance.status != STATUS_RESOLVED, Grievance.due_date < utcnow())
        conds.append(is_od if overdue else ~is_od)
    if escalated is not None:
        conds.append(Grievance.escalated == escalated)
    if report_status:
        conds.append(Grievance.report_status == report_status)
    if q:
        like = f"%{q.strip()}%"
        conds.append(or_(Grievance.subject.ilike(like), Grievance.reference_no.ilike(like)))

    total = db.scalar(select(func.count(Grievance.id)).where(*conds)) or 0
    rows = db.scalars(select(Grievance).where(*conds).options(joinedload(Grievance.department))
                      .order_by(Grievance.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [grievance_summary(g) for g in rows], "total": total, "page": page, "page_size": page_size}


@router.get("/dashboard-summary")
def my_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Counts for the caller's own scope (citizen: own grievances, officer: department)."""
    scope = []
    if user.role == ROLE_CITIZEN:
        scope.append(Grievance.citizen_id == user.id)
    elif user.role == ROLE_OFFICER:
        scope.append(Grievance.department_id == user.department_id)
    rows = dict(db.execute(select(Grievance.status, func.count()).where(*scope).group_by(Grievance.status)).all())
    total = sum(rows.values())
    resolved = rows.get(STATUS_RESOLVED, 0)
    overdue = db.scalar(select(func.count(Grievance.id)).where(
        *scope, Grievance.status != STATUS_RESOLVED, Grievance.due_date < utcnow())) or 0
    return {"total": total, "resolved": resolved, "pending": total - resolved, "overdue": overdue, "by_status": rows}


@router.get("/{reference_no}")
def get_grievance(reference_no: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return grievance_detail(get_grievance_or_404(db, reference_no, user), user)


@router.patch("/{reference_no}/status")
def update_status(reference_no: str, body: StatusIn, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    """Role-checked status transition (see services/workflow.ALLOWED_TRANSITIONS)."""
    g = get_grievance_or_404(db, reference_no, user)
    change_status(db, g, user, body.status, body.remarks)
    db.commit()
    return grievance_detail(g, user)


@router.post("/{reference_no}/remarks")
def add_remark(reference_no: str, body: RemarkIn, user: User = Depends(require_roles(ROLE_CMO, ROLE_OFFICER)),
               db: Session = Depends(get_db)):
    g = get_grievance_or_404(db, reference_no, user)
    if body.visibility not in allowed_visibilities(user.role):
        raise HTTPException(403, "You cannot post remarks with this visibility")
    label = {"public": "Remark added", "department": "Department note added", "internal": "Internal remark added"}
    add_history(db, g, user, label[body.visibility], remarks=body.remarks, visibility=body.visibility)
    db.commit()
    return grievance_detail(g, user)


@router.post("/{reference_no}/feedback", status_code=201)
def give_feedback(reference_no: str, body: FeedbackIn, user: User = Depends(require_roles(ROLE_CITIZEN)),
                  db: Session = Depends(get_db)):
    g = get_grievance_or_404(db, reference_no, user)
    detail = grievance_detail(g, user)
    if not detail["can_give_feedback"]:
        raise HTTPException(400, "Feedback can be given once, after the grievance is resolved")
    db.add(Feedback(grievance=g, citizen_id=user.id, rating=body.rating, comment=body.comment))
    add_history(db, g, user, "Citizen feedback submitted", remarks=f"Rating: {body.rating}/5",
                visibility=VIS_PUBLIC)
    db.commit()
    return {"message": "Thank you for your feedback."}


@router.get("/{reference_no}/attachments/{attachment_id}")
def download_attachment(reference_no: str, attachment_id: int, user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    g = get_grievance_or_404(db, reference_no, user)
    att = db.get(Attachment, attachment_id)
    if att is None or att.grievance_id != g.id:
        raise HTTPException(404, "Attachment not found")
    if user.role == ROLE_CITIZEN and att.kind != "complaint" and g.status != STATUS_RESOLVED:
        raise HTTPException(404, "Attachment not found")
    disposition = "inline" if att.content_type.startswith("image/") or att.content_type == "application/pdf" \
        else "attachment"
    return Response(content=att.data, media_type=att.content_type, headers={
        "Content-Disposition": f'{disposition}; filename="{att.filename}"',
        "X-Content-Type-Options": "nosniff", "Cache-Control": "private, max-age=300"})
