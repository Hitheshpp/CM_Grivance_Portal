from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from ..constants import (REPORT_ACCEPTED, REPORT_PENDING, REPORT_REJECTED, ROLE_CMO, ROLE_OFFICER, STATUS_PROGRESS,
                         STATUS_RESOLVED, STATUS_REVIEW, STATUS_SUBMITTED, STATUSES, VIS_DEPARTMENT, VIS_PUBLIC)
from ..database import get_db
from ..deps import require_roles
from ..models import ContactEnquiry, Department, DepartmentAssignment, Feedback, Grievance, User, utcnow
from ..schemas import AssignIn, EscalateIn, ReportReviewIn, TriageIn
from ..services.workflow import (add_history, apply_status, due_date_for, get_grievance_or_404, grievance_detail)

router = APIRouter(prefix="/api/cmo", tags=["CMO"], dependencies=[Depends(require_roles(ROLE_CMO))])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    """Dashboard figures computed live from stored grievances."""
    now = utcnow()
    total = db.scalar(select(func.count(Grievance.id))) or 0
    resolved = db.scalar(select(func.count(Grievance.id)).where(Grievance.status == STATUS_RESOLVED)) or 0
    overdue = db.scalar(select(func.count(Grievance.id)).where(
        Grievance.status != STATUS_RESOLVED, Grievance.due_date < now)) or 0
    escalated = db.scalar(select(func.count(Grievance.id)).where(
        Grievance.escalated.is_(True), Grievance.status != STATUS_RESOLVED)) or 0
    reports_pending = db.scalar(select(func.count(Grievance.id)).where(
        Grievance.report_status == REPORT_PENDING)) or 0
    unassigned = db.scalar(select(func.count(Grievance.id)).where(
        Grievance.department_id.is_(None), Grievance.status != STATUS_RESOLVED)) or 0

    def grouped(col):
        rows = db.execute(select(col, func.count(Grievance.id)).group_by(col).order_by(func.count().desc())).all()
        return [{"label": r[0] or "Unassigned", "count": r[1]} for r in rows]

    by_dept = db.execute(
        select(Department.name,
               func.count(Grievance.id),
               func.sum(case((Grievance.status == STATUS_RESOLVED, 1), else_=0)),
               func.sum(case((Grievance.status != STATUS_RESOLVED, case((Grievance.due_date < now, 1), else_=0)),
                             else_=0)))
        .join(Grievance, Grievance.department_id == Department.id, isouter=True)
        .group_by(Department.name).order_by(Department.name)).all()
    by_district = db.execute(
        select(Grievance.district, func.count(Grievance.id),
               func.sum(case((Grievance.status == STATUS_RESOLVED, 1), else_=0)))
        .group_by(Grievance.district).order_by(func.count(Grievance.id).desc())).all()
    avg_rating = db.scalar(select(func.avg(Feedback.rating)))

    return {
        "total": total, "resolved": resolved, "pending": total - resolved, "overdue": overdue,
        "escalated": escalated, "reports_pending_review": reports_pending, "unassigned": unassigned,
        "avg_feedback_rating": round(float(avg_rating), 2) if avg_rating else None,
        "by_status": grouped(Grievance.status), "by_category": grouped(Grievance.category),
        "by_priority": grouped(Grievance.priority),
        "by_department": [{"label": r[0], "total": r[1], "resolved": int(r[2] or 0), "overdue": int(r[3] or 0)}
                          for r in by_dept],
        "by_district": [{"label": r[0], "total": r[1], "resolved": int(r[2] or 0)} for r in by_district],
    }


@router.get("/officers")
def officers(department_id: int | None = None, db: Session = Depends(get_db)):
    q = select(User).where(User.role == ROLE_OFFICER, User.is_active.is_(True))
    if department_id:
        q = q.where(User.department_id == department_id)
    return [{"id": u.id, "name": u.name, "department_id": u.department_id,
             "department": u.department.name if u.department else None} for u in db.scalars(q.order_by(User.name))]


@router.get("/enquiries")
def enquiries(db: Session = Depends(get_db)):
    rows = db.scalars(select(ContactEnquiry).order_by(ContactEnquiry.id.desc()).limit(100)).all()
    return [{"id": e.id, "name": e.name, "email": e.email, "subject": e.subject, "message": e.message,
             "created_at": e.created_at} for e in rows]


@router.post("/grievances/{reference_no}/assign")
def assign(reference_no: str, body: AssignIn, user: User = Depends(require_roles(ROLE_CMO)),
           db: Session = Depends(get_db)):
    """Forward (or re-forward) a grievance to a department and optionally a specific officer."""
    g = get_grievance_or_404(db, reference_no, user)
    if g.status == STATUS_RESOLVED:
        raise HTTPException(400, "Resolved grievances cannot be reassigned. Wait for the citizen to reopen it.")
    dept = db.get(Department, body.department_id)
    if dept is None:
        raise HTTPException(404, "Department not found")
    officer = None
    if body.officer_id:
        officer = db.get(User, body.officer_id)
        if officer is None or officer.role != ROLE_OFFICER or officer.department_id != dept.id:
            raise HTTPException(400, "Officer does not belong to the selected department")
    for a in g.assignments:
        a.is_active = False
    db.add(DepartmentAssignment(grievance=g, department_id=dept.id, officer_id=officer.id if officer else None,
                                assigned_by=user.id, note=body.note))
    previously = g.department.name if g.department else None
    g.department, g.officer = dept, officer  # set relationships so the response reflects the new routing
    g.report_status = None
    if g.status == STATUS_SUBMITTED:
        apply_status(db, g, user, STATUS_REVIEW, None, action="CMO review started")
    action = f"Forwarded to {dept.name}" if not previously else f"Reassigned from {previously} to {dept.name}"
    remark = (f"Officer: {officer.name}. " if officer else "") + (body.note or "")
    add_history(db, g, user, action, remarks=remark.strip() or None, visibility=VIS_PUBLIC)
    db.commit()
    return grievance_detail(g, user)


@router.post("/grievances/{reference_no}/escalate")
def escalate(reference_no: str, body: EscalateIn, user: User = Depends(require_roles(ROLE_CMO)),
             db: Session = Depends(get_db)):
    g = get_grievance_or_404(db, reference_no, user)
    if g.status == STATUS_RESOLVED:
        raise HTTPException(400, "Resolved grievances cannot be escalated")
    g.escalated, g.escalated_at = True, utcnow()
    if g.priority != "High":
        g.priority = "High"
        g.due_date = due_date_for("High", g.created_at)
    add_history(db, g, user, "Escalated by CMO", remarks=body.reason, visibility=VIS_DEPARTMENT)
    db.commit()
    return grievance_detail(g, user)


@router.patch("/grievances/{reference_no}/triage")
def triage(reference_no: str, body: TriageIn, user: User = Depends(require_roles(ROLE_CMO)),
           db: Session = Depends(get_db)):
    """CMO reviews the AI suggestion: confirm or override category/priority. Recorded in the audit trail."""
    g = get_grievance_or_404(db, reference_no, user)
    changes = []
    if body.category and body.category != g.category:
        changes.append(f"Category: {g.category} -> {body.category}")
        g.category = body.category
    if body.priority and body.priority != g.priority:
        changes.append(f"Priority: {g.priority} -> {body.priority}")
        g.priority = body.priority
        g.due_date = due_date_for(body.priority, g.created_at)
    g.ai_reviewed, g.ai_reviewed_by, g.ai_reviewed_at = True, user.id, utcnow()
    summary = "; ".join(changes) if changes else "AI suggestion confirmed without changes"
    add_history(db, g, user, "CMO reviewed AI triage", remarks=f"{summary}. {body.remarks or ''}".strip(),
                visibility=VIS_DEPARTMENT)
    db.commit()
    return grievance_detail(g, user)


@router.post("/grievances/{reference_no}/review-report")
def review_report(reference_no: str, body: ReportReviewIn, user: User = Depends(require_roles(ROLE_CMO)),
                  db: Session = Depends(get_db)):
    """CMO accepts the department's action-taken report (-> Resolved) or sends it back (-> In Progress)."""
    g = get_grievance_or_404(db, reference_no, user)
    if g.report_status != REPORT_PENDING:
        raise HTTPException(400, "There is no action-taken report awaiting review")
    if body.decision == "accept":
        g.report_status = REPORT_ACCEPTED
        apply_status(db, g, user, STATUS_RESOLVED, body.remarks or "Action-taken report accepted",
                     action="Resolved: report accepted by CMO")
    else:
        if not (body.remarks and body.remarks.strip()):
            raise HTTPException(400, "Remarks are required when sending a report back")
        g.report_status = REPORT_REJECTED
        apply_status(db, g, user, STATUS_PROGRESS, body.remarks, action="Report returned to department")
    db.commit()
    return grievance_detail(g, user)
