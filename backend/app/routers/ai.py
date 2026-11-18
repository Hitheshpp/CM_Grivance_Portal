from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..constants import ROLE_CITIZEN, ROLE_CMO
from ..database import get_db
from ..deps import require_roles
from ..models import User
from ..schemas import AnalyzeIn
from ..security import RateLimiter
from ..services import ai_service

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])
ai_limit = RateLimiter(15, 60, "AI analysis")


@router.post("/analyze", dependencies=[Depends(ai_limit)])
def analyze(body: AnalyzeIn, _: User = Depends(require_roles(ROLE_CITIZEN, ROLE_CMO)), db: Session = Depends(get_db)):
    """Advisory analysis of complaint text: department, category, priority, CMO summary, possible duplicates.
    Nothing is saved or decided here; the citizen/CMO reviews the suggestion."""
    return ai_service.analyze(db, body.description, body.subject, body.district)
