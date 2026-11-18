import uuid
from datetime import datetime, timezone

from sqlalchemy import (JSON, Boolean, DateTime, ForeignKey, Integer, LargeBinary, String, Text,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    description: Mapped[str] = mapped_column(Text)
    default_category: Mapped[str | None] = mapped_column(String(60))


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    mobile: Mapped[str] = mapped_column(String(15))
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), index=True)  # citizen | cmo | officer
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    department: Mapped[Department | None] = relationship()


class Grievance(Base):
    __tablename__ = "grievances"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference_no: Mapped[str] = mapped_column(String(32), unique=True, index=True,
                                              default=lambda: "TMP-" + uuid.uuid4().hex[:20])
    citizen_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    district: Mapped[str] = mapped_column(String(40), index=True)
    category: Mapped[str] = mapped_column(String(60), index=True)
    subject: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(10), default="Medium", index=True)
    status: Mapped[str] = mapped_column(String(20), default="Submitted", index=True)

    # current routing (full trail lives in department_assignments)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), index=True)
    assigned_officer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    escalated: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # action-taken report submitted by the department
    report_text: Mapped[str | None] = mapped_column(Text)
    report_status: Mapped[str | None] = mapped_column(String(30))
    report_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # AI suggestions (advisory only - never an official decision)
    ai_department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"))
    ai_category: Mapped[str | None] = mapped_column(String(60))
    ai_priority: Mapped[str | None] = mapped_column(String(10))
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_provider: Mapped[str | None] = mapped_column(String(60))
    ai_is_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_duplicates: Mapped[list | None] = mapped_column(JSON)
    ai_reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    ai_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    citizen: Mapped[User] = relationship(foreign_keys=[citizen_id])
    department: Mapped[Department | None] = relationship(foreign_keys=[department_id])
    ai_department: Mapped[Department | None] = relationship(foreign_keys=[ai_department_id])
    officer: Mapped[User | None] = relationship(foreign_keys=[assigned_officer_id])
    history: Mapped[list["GrievanceHistory"]] = relationship(
        back_populates="grievance", order_by="GrievanceHistory.id", cascade="all, delete-orphan")
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="grievance", order_by="Attachment.id", cascade="all, delete-orphan")
    assignments: Mapped[list["DepartmentAssignment"]] = relationship(
        back_populates="grievance", order_by="DepartmentAssignment.id", cascade="all, delete-orphan")
    feedback: Mapped[list["Feedback"]] = relationship(
        back_populates="grievance", order_by="Feedback.id", cascade="all, delete-orphan")


class GrievanceHistory(Base):
    """Append-only audit trail: every status change/action with timestamp and responsible user."""
    __tablename__ = "grievance_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    grievance_id: Mapped[int] = mapped_column(ForeignKey("grievances.id"), index=True)
    action: Mapped[str] = mapped_column(String(80))
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20))
    remarks: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[str] = mapped_column(String(12), default="public")
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    actor_role: Mapped[str] = mapped_column(String(20), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    grievance: Mapped[Grievance] = relationship(back_populates="history")
    actor: Mapped[User | None] = relationship()


class DepartmentAssignment(Base):
    __tablename__ = "department_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    grievance_id: Mapped[int] = mapped_column(ForeignKey("grievances.id"), index=True)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"))
    officer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    assigned_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    note: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    grievance: Mapped[Grievance] = relationship(back_populates="assignments")
    department: Mapped[Department] = relationship()
    officer: Mapped[User | None] = relationship(foreign_keys=[officer_id])
    assigner: Mapped[User] = relationship(foreign_keys=[assigned_by])


class Attachment(Base):
    """Files are stored in the database so they survive ephemeral hosting file systems."""
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    grievance_id: Mapped[int] = mapped_column(ForeignKey("grievances.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20), default="complaint")  # complaint | action_report
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size: Mapped[int] = mapped_column(Integer)
    data: Mapped[bytes] = mapped_column(LargeBinary, deferred=True)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    grievance: Mapped[Grievance] = relationship(back_populates="attachments")


class Feedback(Base):
    __tablename__ = "citizen_feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    grievance_id: Mapped[int] = mapped_column(ForeignKey("grievances.id"), index=True)
    citizen_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    grievance: Mapped[Grievance] = relationship(back_populates="feedback")


class ContactEnquiry(Base):
    __tablename__ = "contact_enquiries"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
