from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..constants import REPORT_PENDING, ROLE_OFFICER, STATUS_PROGRESS, VIS_PUBLIC
from ..database import get_db
from ..deps import require_roles
from ..models import User, utcnow
from ..services import files
from ..services.workflow import add_history, get_grievance_or_404, grievance_detail

router = APIRouter(prefix="/api/officer", tags=["Department Officer"])


@router.post("/grievances/{reference_no}/report")
def submit_report(
    reference_no: str, report_text: str = Form(..., min_length=20, max_length=8000),
    file: UploadFile | None = File(None), user: User = Depends(require_roles(ROLE_OFFICER)),
    db: Session = Depends(get_db),
):
    """Submit the action-taken report (text and/or supporting document) back to the CMO for review."""
    g = get_grievance_or_404(db, reference_no, user)  # 404 unless it belongs to the officer's department
    if g.status != STATUS_PROGRESS:
        raise HTTPException(400, "Mark the grievance 'In Progress' before submitting an action-taken report")
    if g.report_status == REPORT_PENDING:
        raise HTTPException(400, "A report is already awaiting CMO review")
    g.report_text, g.report_status, g.report_submitted_at = report_text.strip(), REPORT_PENDING, utcnow()
    if file is not None and file.filename:
        files.attach(g, file, user, "action_report")
    add_history(db, g, user, "Action-taken report submitted to CMO", remarks="Awaiting CMO review",
                visibility=VIS_PUBLIC)
    db.commit()
    return grievance_detail(g, user)
