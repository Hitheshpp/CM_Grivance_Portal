# 04 – API Documentation

Base URL: `http://localhost:8001` (local) · interactive OpenAPI/Swagger UI at **`/docs`**, schema at `/openapi.json`.

- Format: JSON (`application/json`), except uploads which use `multipart/form-data`.
- Auth: `Authorization: Bearer <JWT>` (obtained from login/register; expires in 8 h).
- Errors: `{"detail": "message"}` or, for validation errors (422), `{"detail": [{"loc": [...], "msg": "..."}]}`.
- Common status codes: 400 rule violation · 401 not authenticated · 403 wrong role · 404 not found / not yours ·
  409 duplicate · 413 file too large · 415 bad file type · 422 validation · 429 rate limited.
- `{ref}` is the grievance reference number, e.g. `KGR-2026-000012`.

## Summary
| Area | Method & path | Role |
|---|---|---|
| Health | `GET /api/health` | public |
| Public | `GET /api/public/meta`, `/departments`, `/stats` · `POST /api/public/contact` · `GET /api/public/track/{ref}` | public |
| Auth | `POST /api/auth/register` · `POST /api/auth/login` · `POST /api/auth/logout` · `GET /api/auth/me` | public / any |
| AI | `POST /api/ai/analyze` | citizen, cmo |
| Grievances | `POST /api/grievances` (submit) | citizen |
| | `GET /api/grievances` (list, role-scoped, filters) | any |
| | `GET /api/grievances/dashboard-summary` | any |
| | `GET /api/grievances/{ref}` | owner / dept officer / cmo |
| | `PATCH /api/grievances/{ref}/status` | role-checked transitions |
| | `POST /api/grievances/{ref}/remarks` | cmo, officer |
| | `POST /api/grievances/{ref}/feedback` | citizen (owner) |
| | `GET /api/grievances/{ref}/attachments/{id}` | any authorised viewer |
| CMO | `GET /api/cmo/stats` · `/officers` · `/enquiries` | cmo |
| | `POST /api/cmo/grievances/{ref}/assign` · `/escalate` · `/review-report` | cmo |
| | `PATCH /api/cmo/grievances/{ref}/triage` | cmo |
| | `POST /api/cmo/officers` · `PATCH /api/cmo/officers/{id}/active` · `POST /api/cmo/officers/{id}/reset-password` | cmo |
| Officer | `POST /api/officer/grievances/{ref}/report` | officer |

---
## Auth
### POST /api/auth/register
Creates a **citizen** (role cannot be chosen). Rate limit 5/min/IP.
```json
// request
{ "name": "Test User", "email": "test@demo-portal.in", "mobile": "9876543210", "password": "Passw0rdX" }
// 201 response
{ "access_token": "eyJ...", "token_type": "bearer",
  "user": { "id": 12, "name": "Test User", "email": "test@demo-portal.in", "mobile": "9876543210",
            "role": "citizen", "department_id": null, "department": null } }
```
Rules: mobile = 10-digit Indian number (optional +91); password 8–64 chars with a letter and a digit. 409 if email exists.

### POST /api/auth/login
```json
{ "email": "cmo@demo-portal.in", "password": "Demo@1234" }
```
Returns the same shape as register. 401 `Invalid email or password` for any failure. Rate limit 10/min/IP.

### POST /api/auth/logout · GET /api/auth/me
Logout is stateless (client discards the token). `me` returns the current user object.

## Public
### GET /api/public/departments
```json
[{ "id": 1, "code": "PWD", "name": "Public Works Department", "description": "Roads, bridges…", "category": "Roads & Infrastructure" }]
```
### GET /api/public/stats
`{"total_grievances": 34, "resolved": 13, "resolution_rate": 38, "departments": 10, "districts_covered": 14}`
### POST /api/public/contact
`{"name":"Ann","email":"ann@demo-portal.in","subject":"Question","message":"How long does it take?"}` → 201 `{"message": "..."}` (saved in `contact_enquiries`).
### GET /api/public/track/{ref}
Returns status, department and **public** history only (no description, personal data, attachments or internal notes).
```json
{ "reference_no": "KGR-2026-000012", "subject": "...", "district": "Kollam", "category": "Healthcare",
  "status": "In Progress", "priority": "High", "department": "Health & Family Welfare", "overdue": false,
  "created_at": "...", "updated_at": "...",
  "history": [{ "action": "Grievance submitted", "from_status": null, "to_status": "Submitted", "remarks": "...",
                "created_at": "...", "actor_role": "citizen" }] }
```

## AI
### POST /api/ai/analyze  (citizen, cmo; 15/min/IP)
```json
// request (description 20–5000 chars)
{ "description": "There is a large pothole near the bus stand, dangerous for children…",
  "subject": "Pothole", "district": "Ernakulam" }
// 200 response
{ "category": "Roads & Infrastructure", "priority": "High",
  "summary": "Large pothole near bus stand endangering schoolchildren.",
  "reasoning": "Road defect with safety risk", "department_id": 1, "department_name": "Public Works Department",
  "provider": "anthropic", "model": "claude-haiku-5-5", "is_fallback": false, "note": null,
  "duplicates": [{ "reference_no": "KGR-2026-000031", "subject": "...", "status": "Submitted", "similarity": 0.62 }],
  "disclaimer": "AI-generated suggestion for human review. It is not an official decision." }
```
When no key is configured or the provider fails: `"provider": "keyword-fallback", "is_fallback": true, "note": "…fallback used."`.

## Grievances
### POST /api/grievances (multipart, citizen)
Fields: `district`, `category`, `subject` (5–200), `description` (20–5000), `priority` (optional), `file` (optional PDF/JPEG/PNG/WEBP ≤ 5 MB).
```bash
curl -X POST $API/api/grievances -H "Authorization: Bearer $TOKEN" \
  -F district=Ernakulam -F category="Roads & Infrastructure" -F subject="Pothole near bus stand" \
  -F description="Large pothole dangerous for children…" -F priority=High -F file=@photo.png
```
201: `{"reference_no":"KGR-2026-000035","status":"Submitted","due_date":"...","message":"..."}`

### GET /api/grievances
Query: `status, district, category, priority, department_id (cmo), overdue (true|false), escalated, report_status, q, page, page_size (≤100)`.
Scope: citizen → own; officer → own department; cmo → all.
```json
{ "items": [{ "reference_no": "...", "subject": "...", "district": "...", "category": "...", "priority": "High",
              "status": "Under Review", "department": "Public Works Department", "department_id": 1,
              "created_at": "...", "updated_at": "...", "due_date": "...", "overdue": false,
              "escalated": false, "report_status": null }],
  "total": 34, "page": 1, "page_size": 10 }
```
### GET /api/grievances/dashboard-summary
`{"total": 7, "resolved": 2, "pending": 5, "overdue": 1, "by_status": {"Resolved": 2, …}}` (scoped like the list).

### GET /api/grievances/{ref}
Full detail: summary fields + `description`, `history[]` (filtered by role), `attachments[]`, `feedback[]`,
`can_give_feedback`, `action_taken_report`, `ai` (suggestion + notice), and for staff `citizen`, `assignments[]`.
Citizens receive the action-taken report only when `status = Resolved`.

### PATCH /api/grievances/{ref}/status
`{"status": "In Progress", "remarks": "Site visit scheduled"}` – allowed transitions:

| Role | Allowed |
|---|---|
| citizen | Resolved → Reopened (remarks/reason **required**) |
| officer | Under Review → In Progress; Reopened → In Progress |
| cmo | Submitted → Under Review; Under Review ⇄ In Progress; Reopened → Under Review / In Progress |

`Resolved` is **only** set via `POST /api/cmo/grievances/{ref}/review-report`. Anything else → 400.

### POST /api/grievances/{ref}/remarks (cmo, officer)
`{"remarks": "Contractor engaged", "visibility": "public|department|internal"}` (officers cannot use `internal`).

### POST /api/grievances/{ref}/feedback (citizen, after Resolved, once per resolution)
`{"rating": 5, "comment": "Fixed, thank you"}` → 201.

### GET /api/grievances/{ref}/attachments/{id}
Returns the file with `Content-Type`, `Content-Disposition`, `X-Content-Type-Options: nosniff`. Requires Bearer token.

## CMO
### GET /api/cmo/stats
```json
{ "total": 34, "resolved": 13, "pending": 21, "overdue": 17, "escalated": 0, "reports_pending_review": 3,
  "unassigned": 2, "avg_feedback_rating": 4.14,
  "by_status": [{"label":"Resolved","count":13}], "by_category": [...], "by_priority": [...],
  "by_department": [{"label":"Agriculture","total":2,"resolved":0,"overdue":2}],
  "by_district": [{"label":"Kollam","total":3,"resolved":1}] }
```
### POST /api/cmo/grievances/{ref}/assign
`{"department_id": 1, "officer_id": 4, "note": "Please inspect urgently"}` – `officer_id` optional and must belong to the department.
Moves `Submitted → Under Review` automatically, records a `department_assignments` row and a history entry.
### PATCH /api/cmo/grievances/{ref}/triage
`{"category": "Healthcare", "priority": "High", "remarks": "…"}` – confirms/overrides AI suggestion (recorded in history; priority change recomputes due date).
### POST /api/cmo/grievances/{ref}/escalate
`{"reason": "Delayed beyond SLA"}` → sets `escalated`, priority High, department-visible history entry.
### POST /api/cmo/grievances/{ref}/review-report
`{"decision": "accept"|"reject", "remarks": "…"}` – accept → **Resolved**; reject (remarks required) → back to **In Progress**.
### GET /api/cmo/officers?department_id=&include_inactive=
Lists officers (`id, name, email, mobile, is_active, department_id, department`). Active only by default.
### POST /api/cmo/officers
Creates an officer account with a temporary password. 201 returns the officer (never the password); 409 duplicate email; 404 unknown department.
```json
{ "name": "Meera Das", "email": "meera.das@demo-portal.in", "mobile": "9876501234", "password": "TempPass1", "department_id": 1 }
```
### PATCH /api/cmo/officers/{id}/active · POST /api/cmo/officers/{id}/reset-password
`{"is_active": false}` blocks login immediately (existing tokens stop working; history is kept). `{"password": "NewPass99"}` resets the password.
Only officer accounts can be managed through these endpoints (404 for CMO/citizen ids).
### GET /api/cmo/enquiries

## Officer
### POST /api/officer/grievances/{ref}/report (multipart)
Fields: `report_text` (20–8000), `file` (optional). Requires status **In Progress** and no report already pending.
Sets `report_status = "Pending CMO Review"`.
