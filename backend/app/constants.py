ROLE_CITIZEN = "citizen"
ROLE_CMO = "cmo"
ROLE_OFFICER = "officer"
ROLES = (ROLE_CITIZEN, ROLE_CMO, ROLE_OFFICER)

STATUS_SUBMITTED = "Submitted"
STATUS_REVIEW = "Under Review"
STATUS_PROGRESS = "In Progress"
STATUS_RESOLVED = "Resolved"
STATUS_REOPENED = "Reopened"
STATUSES = (STATUS_SUBMITTED, STATUS_REVIEW, STATUS_PROGRESS, STATUS_RESOLVED, STATUS_REOPENED)

PRIORITIES = ("Low", "Medium", "High")
# Days allowed before a grievance is considered overdue, by priority.
SLA_DAYS = {"High": 7, "Medium": 15, "Low": 30}

REPORT_PENDING = "Pending CMO Review"
REPORT_ACCEPTED = "Accepted"
REPORT_REJECTED = "Rejected"

# Remark visibility: public = citizen+officer+CMO, department = officer+CMO, internal = CMO only
VIS_PUBLIC = "public"
VIS_DEPARTMENT = "department"
VIS_INTERNAL = "internal"
VISIBILITIES = (VIS_PUBLIC, VIS_DEPARTMENT, VIS_INTERNAL)

DISTRICTS = [
    "Thiruvananthapuram", "Kollam", "Pathanamthitta", "Alappuzha", "Kottayam", "Idukki", "Ernakulam",
    "Thrissur", "Palakkad", "Malappuram", "Kozhikode", "Wayanad", "Kannur", "Kasaragod",
]

CATEGORIES = [
    "Roads & Infrastructure", "Healthcare", "Education", "Water & Sanitation", "Electricity",
    "Public Services", "Law & Order", "Social Welfare", "Agriculture", "Environment", "Other",
]

ALLOWED_UPLOAD_TYPES = {
    "application/pdf": (b"%PDF",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG",),
    "image/webp": (b"RIFF",),
}
