import re

from fastapi import HTTPException, UploadFile

from ..config import get_settings
from ..constants import ALLOWED_UPLOAD_TYPES
from ..models import Attachment, Grievance, User


def safe_filename(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", (name or "file").split("/")[-1].split("\\")[-1])
    return name[:150] or "file"


def read_validated_upload(file: UploadFile) -> tuple[bytes, str]:
    """Return (bytes, content_type) after checking size, declared type and file signature."""
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(413, f"File too large (max {get_settings().max_upload_mb} MB)")
    if not data:
        raise HTTPException(400, "Uploaded file is empty")
    ctype = file.content_type or ""
    if ctype not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(415, "Only PDF, JPEG, PNG or WEBP files are allowed")
    if not any(data.startswith(sig) for sig in ALLOWED_UPLOAD_TYPES[ctype]):
        raise HTTPException(415, "File content does not match its declared type")
    return data, ctype


def attach(grievance: Grievance, file: UploadFile, user: User, kind: str) -> Attachment:
    data, ctype = read_validated_upload(file)
    att = Attachment(grievance=grievance, kind=kind, filename=safe_filename(file.filename), content_type=ctype,
                     size=len(data), data=data, uploaded_by=user.id)
    return att
