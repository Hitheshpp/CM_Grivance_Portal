"""Grievance lifecycle rules, access control and serialization.

Workflow: Submitted -> Under Review (CMO) -> forwarded to department -> In Progress (officer)
-> action-taken report -> CMO review -> Resolved (or back to In Progress) -> citizen may Reopen.
"""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..constants import (ROLE_CITIZEN, ROLE_CMO, ROLE_OFFICER, SLA_DAYS, STATUS_PROGRESS, STATUS_REOPENED,
                         STATUS_RESOLVED, STATUS_REVIEW, STATUS_SUBMITTED, VIS_DEPARTMENT, VIS_INTERNAL,
                         VIS_PUBLIC)
from ..models import Grievance, GrievanceHistory, User, utcnow

# (from_status, to_status) pairs each role may perform through the generic status endpoint.
# Resolved is deliberately NOT here: it is only reachable via CMO review of an action-taken report.
ALLOWED_TRANSITIONS = {
    ROLE_CMO: {
        (STATUS_SUBMITTED, STATUS_REVIEW), (STATUS_REVIEW, STATUS_PROGRESS),
        (STATUS_PROGRESS, STATUS_REVIEW), (STATUS_REOPENED, STATUS_REVIEW), (STATUS_REOPENED, STATUS_PROGRESS),
    },
    ROLE_OFFICER: {(STATUS_REVIEW, STATUS_PROGRESS), (STATUS_REOPENED, STATUS_PROGRESS)},
    ROLE_CITIZEN: {(STATUS_RESOLVED, STATUS_REOPENED)},
}


def aware(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def due_date_for(priority: str, start: datetime | None = None) -> datetime:
    return (start or utcnow()) + timedelta(days=SLA_DAYS.get(priority, SLA_DAYS["Medium"]))


def is_overdue(g: Grievance) -> bool:
    return g.status != STATUS_RESOLVED and aware(g.due_date) < utcnow()


def add_history(db: Session, g: Grievance, user: User | None, action: str, to_status: str | None = None,
                remarks: str | None = None, visibility: str = VIS_PUBLIC, from_status: str | None = None) -> None:
    db.add(GrievanceHistory(
        grievance=g, action=action, from_status=from_status or g.status, to_status=to_status or g.status,
        remarks=remarks, visibility=visibility, actor_id=user.id if user else None,
        actor_role=user.role if user else "system"))


def change_status(db: Session, g: Grievance, user: User, new_status: str, remarks: str | None,
                  visibility: str = VIS_PUBLIC, action: str | None = None) -> None:
    old = g.status
    if (old, new_status) not in ALLOWED_TRANSITIONS.get(user.role, set()):
        raise HTTPException(400, f"Role '{user.role}' cannot change status from '{old}' to '{new_status}'")
    if new_status == STATUS_REOPENED and not (remarks and remarks.strip()):
        raise HTTPException(400, "A reason is required to reopen a grievance")
    apply_status(db, g, user, new_status, remarks, visibility, action)


def apply_status(db: Session, g: Grievance, user: User, new_status: str, remarks: str | None,
                 visibility: str = VIS_PUBLIC, action: str | None = None) -> None:
    """Unchecked status change; callers are responsible for authorisation."""
    old = g.status
    g.status = new_status
    if new_status == STATUS_RESOLVED:
        g.resolved_at = utcnow()
    if new_status == STATUS_REOPENED:
        g.resolved_at = None
        g.report_status = None
        g.due_date = due_date_for(g.priority)  # fresh SLA window after reopening
    add_history(db, g, user, action or f"Status changed to {new_status}", new_status, remarks, visibility, old)


# ---------------------------------------------------------------- access control
def can_view(user: User, g: Grievance) -> bool:
    if user.role == ROLE_CMO:
        return True
    if user.role == ROLE_CITIZEN:
        return g.citizen_id == user.id
    if user.role == ROLE_OFFICER:
        return g.department_id is not None and g.department_id == user.department_id
    return False


def get_grievance_or_404(db: Session, ref: str, user: User) -> Grievance:
    from sqlalchemy import select
    g = db.scalar(select(Grievance).where(Grievance.reference_no == ref))
    # Same 404 for "missing" and "not yours" so references cannot be enumerated.
    if g is None or not can_view(user, g):
        raise HTTPException(404, "Grievance not found")
    return g


def allowed_visibilities(role: str) -> set[str]:
    if role == ROLE_CMO:
        return {VIS_PUBLIC, VIS_DEPARTMENT, VIS_INTERNAL}
    if role == ROLE_OFFICER:
        return {VIS_PUBLIC, VIS_DEPARTMENT}
    return {VIS_PUBLIC}


# ---------------------------------------------------------------- serialization
def history_out(h: GrievanceHistory, role: str) -> dict:
    return {
        "id": h.id, "action": h.action, "from_status": h.from_status, "to_status": h.to_status,
        "remarks": h.remarks, "visibility": h.visibility, "created_at": h.created_at,
        "actor_name": h.actor.name if h.actor else "System",
        # citizens see roles, not names of officials
        "actor_role": h.actor_role,
    } if role != ROLE_CITIZEN else {
        "id": h.id, "action": h.action, "from_status": h.from_status, "to_status": h.to_status,
        "remarks": h.remarks, "created_at": h.created_at, "actor_role": h.actor_role,
    }


def grievance_summary(g: Grievance) -> dict:
    return {
        "reference_no": g.reference_no, "subject": g.subject, "district": g.district, "category": g.category,
        "priority": g.priority, "status": g.status, "department": g.department.name if g.department else None,
        "department_id": g.department_id, "created_at": g.created_at, "updated_at": g.updated_at,
        "due_date": g.due_date, "overdue": is_overdue(g), "escalated": g.escalated,
        "report_status": g.report_status,
    }


def attachment_out(a) -> dict:
    return {"id": a.id, "filename": a.filename, "content_type": a.content_type, "size": a.size,
            "kind": a.kind, "uploaded_at": a.uploaded_at}


def ai_out(g: Grievance) -> dict | None:
    if not g.ai_provider:
        return None
    return {
        "department": g.ai_department.name if g.ai_department else None, "category": g.ai_category,
        "priority": g.ai_priority, "summary": g.ai_summary, "provider": g.ai_provider,
        "is_fallback": g.ai_is_fallback, "duplicates": g.ai_duplicates or [],
        "reviewed_by_human": g.ai_reviewed,
        "notice": "AI suggestions are advisory only and require human review.",
    }


def grievance_detail(g: Grievance, user: User) -> dict:
    role = user.role
    vis = allowed_visibilities(role)
    out = grievance_summary(g)
    out.update({
        "description": g.description,
        "history": [history_out(h, role) for h in g.history if h.visibility in vis],
        "attachments": [attachment_out(a) for a in g.attachments
                        if a.kind == "complaint" or role != ROLE_CITIZEN or g.status == STATUS_RESOLVED],
        "feedback": [{"id": f.id, "rating": f.rating, "comment": f.comment, "created_at": f.created_at}
                     for f in g.feedback],
        "can_give_feedback": (role == ROLE_CITIZEN and g.status == STATUS_RESOLVED
                              and not any(aware(f.created_at) >= aware(g.resolved_at) for f in g.feedback)),
    })
    if role == ROLE_CITIZEN:
        # Citizens only see the final report once the CMO has approved it.
        out["action_taken_report"] = g.report_text if g.status == STATUS_RESOLVED else None
    else:
        out.update({
            "action_taken_report": g.report_text, "report_submitted_at": g.report_submitted_at,
            "citizen": {"name": g.citizen.name, "email": g.citizen.email, "mobile": g.citizen.mobile},
            "assigned_officer": g.officer.name if g.officer else None, "ai": ai_out(g),
            "assignments": [{"department": a.department.name, "officer": a.officer.name if a.officer else None,
                             "assigned_by": a.assigner.name, "note": a.note, "is_active": a.is_active,
                             "assigned_at": a.assigned_at} for a in g.assignments],
        })
        if role == ROLE_OFFICER:
            out.pop("citizen")  # officers get the complaint, not unnecessary personal data
            out["citizen_name"] = g.citizen.name
            out.pop("ai", None)
    if role == ROLE_CITIZEN:
        out["ai"] = ai_out(g)
    return out
