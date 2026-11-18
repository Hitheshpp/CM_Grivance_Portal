import re

from pydantic import BaseModel, EmailStr, Field, field_validator

from .constants import CATEGORIES, DISTRICTS, PRIORITIES, STATUSES, VISIBILITIES

MOBILE_RE = re.compile(r"^[6-9]\d{9}$")  # 10-digit Indian mobile number


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    mobile: str
    password: str = Field(min_length=8, max_length=64)

    @field_validator("mobile")
    @classmethod
    def _mobile(cls, v: str) -> str:
        v = v.strip().replace(" ", "")
        if v.startswith("+91"):
            v = v[3:]
        if not MOBILE_RE.match(v):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return v

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
            raise ValueError("Password must contain at least one letter and one digit")
        return v

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        return v.strip()


class OfficerCreateIn(RegisterIn):
    """CMO-created department officer account (temporary password is handed over out-of-band)."""
    department_id: int


class OfficerActiveIn(BaseModel):
    is_active: bool


class PasswordResetIn(BaseModel):
    password: str = Field(min_length=8, max_length=64)

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
            raise ValueError("Password must contain at least one letter and one digit")
        return v


class LoginIn(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(max_length=64)


class ContactIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    subject: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=10, max_length=3000)


class AnalyzeIn(BaseModel):
    description: str = Field(min_length=20, max_length=5000)
    subject: str = Field(default="", max_length=200)
    district: str = ""

    @field_validator("district")
    @classmethod
    def _district(cls, v: str) -> str:
        if v and v not in DISTRICTS:
            raise ValueError("Unknown district")
        return v


class StatusIn(BaseModel):
    status: str
    remarks: str | None = Field(default=None, max_length=2000)

    @field_validator("status")
    @classmethod
    def _status(cls, v: str) -> str:
        if v not in STATUSES:
            raise ValueError(f"Status must be one of {', '.join(STATUSES)}")
        return v


class RemarkIn(BaseModel):
    remarks: str = Field(min_length=2, max_length=2000)
    visibility: str = "public"

    @field_validator("visibility")
    @classmethod
    def _vis(cls, v: str) -> str:
        if v not in VISIBILITIES:
            raise ValueError("Invalid visibility")
        return v


class AssignIn(BaseModel):
    department_id: int
    officer_id: int | None = None
    note: str | None = Field(default=None, max_length=1000)


class EscalateIn(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)


class TriageIn(BaseModel):
    """CMO review of the AI suggestion; omitted fields are kept as-is."""
    category: str | None = None
    priority: str | None = None
    remarks: str | None = Field(default=None, max_length=1000)

    @field_validator("category")
    @classmethod
    def _cat(cls, v):
        if v is not None and v not in CATEGORIES:
            raise ValueError("Unknown category")
        return v

    @field_validator("priority")
    @classmethod
    def _prio(cls, v):
        if v is not None and v not in PRIORITIES:
            raise ValueError("Priority must be Low, Medium or High")
        return v


class ReportReviewIn(BaseModel):
    decision: str  # accept | reject
    remarks: str | None = Field(default=None, max_length=2000)

    @field_validator("decision")
    @classmethod
    def _dec(cls, v: str) -> str:
        if v not in ("accept", "reject"):
            raise ValueError("decision must be 'accept' or 'reject'")
        return v


class FeedbackIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)
