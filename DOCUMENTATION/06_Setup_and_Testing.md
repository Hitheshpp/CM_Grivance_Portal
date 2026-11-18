# 06 – Setup and Testing

## Prerequisites
Python 3.12, Node.js ≥ 20, PostgreSQL 14+ (a local install, or a hosted free database such as Neon/Supabase/Render).

## 1. Database
Create an empty database and a user, then note the connection string:
```sql
CREATE USER cmgrp WITH PASSWORD 'choose-a-password';
CREATE DATABASE cmgrp OWNER cmgrp;
-- DATABASE_URL=postgresql+psycopg://cmgrp:choose-a-password@localhost:5432/cmgrp
```
Tables are created automatically and fictional demo data is seeded on first start when the DB is empty.

## 2. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env                                   # then edit values
uvicorn app.main:app --reload --port 8001
```
API: http://localhost:8001 · Swagger: http://localhost:8001/docs · health: `/api/health`.
Re-seed manually: `python -m app.seed` (only runs on an empty database).

## 3. Frontend
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8001" > .env
npm run dev          # http://localhost:5173
npm run build        # production bundle in dist/
```

## Environment variables
| Variable | Default / example | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://user:pass@host:5432/db` | PostgreSQL (`postgres://` URLs are auto-converted) |
| `JWT_SECRET` | long random string | **Must be changed** in any deployed environment |
| `ACCESS_TOKEN_MINUTES` | `480` | Token lifetime |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed frontend origins |
| `AI_PROVIDER` | `openai` \| `anthropic` \| `gemini` \| `none` | LLM provider |
| `OPENAI_API_KEY`, `OPENAI_MODEL` | – / `gpt-4o-mini` | OpenAI settings |
| `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | – / `claude-haiku-5-5` | Anthropic settings |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | – / `gemini-2.5-flash` | Gemini settings |
| `AI_TIMEOUT_SECONDS` | `20` | LLM timeout |
| `MAX_UPLOAD_MB` | `5` | Upload limit |
| `SEED_ON_STARTUP` | `true` | Seed demo data when DB is empty |
| `VITE_API_URL` (frontend) | `http://localhost:8001` | Backend base URL (build-time) |

## Demo accounts (fictional) – password `Demo@1234`
| Role | Email |
|---|---|
| CMO administrator | `cmo@demo-portal.in` |
| Citizens | `citizen1@demo-portal.in` … `citizen5@demo-portal.in` |
| Department officers | `officer.<code>@demo-portal.in`, code ∈ pwd, health, edu, water, power, lsgd, home, sjd, agri, env |

## Automated tests
```bash
cd backend && pytest -q
```
Runs 22 tests against an in-memory SQLite database with `AI_PROVIDER=none` (no network, no paid API). They cover
registration/login, RBAC, rate limiting, public tracking privacy, AI fallback + validation, duplicate detection, the **full
lifecycle** (submit → triage → assign → in progress → report → reject → resubmit → accept → feedback → reopen → audit trail),
attachment access control, upload validation (type/signature/size), list filters/statistics and escalation.
The same flows were also smoke-tested against real PostgreSQL.

## Manual test cases
| # | Scenario | Steps | Expected |
|---|---|---|---|
| 1 | Register & login | Register with valid data; logout; login | Lands on citizen dashboard; invalid mobile/short password rejected |
| 2 | Submit with AI | Citizen → Submit → type description → *Analyse* → *Use suggested* → upload PNG → Submit | Suggestion shown (AI or labelled FALLBACK); reference `KGR-…` displayed |
| 3 | Track | Track page → paste reference | Status, department, public history shown; no personal data |
| 4 | CMO triage & forward | CMO → All grievances → open → *Confirm triage* → Forward to department/officer | Status Under Review; assignment and history rows appear |
| 5 | Officer work | Officer of that department → open → *Mark In Progress* → add remark → submit report | CMO sees *Report pending* |
| 6 | Isolation | Officer of another department opens the URL | "Grievance not found" |
| 7 | Review report | CMO → *Return* without remarks (error) → with remarks (back to In Progress) → officer resubmits → *Accept* | Status Resolved |
| 8 | Citizen closure | Citizen opens resolved grievance → rate → (optionally) Reopen with reason | Feedback saved once; Reopened with new target date |
| 9 | Filters/stats | CMO → filter by district/category/priority/status/overdue; open Overview | Counts match list totals; charts render |
| 10 | Upload security | Upload `.exe` or renamed text as `.pdf`, or > 5 MB | 415 / 415 / 413 |
| 11 | Contact form | Submit contact form; CMO → Contact enquiries | Enquiry listed |
| 12 | Manage officers | CMO → Manage officers → create officer → log in as them in a private window → deactivate → login fails | Officer sees only own department; deactivated account is blocked |
| 13 | AI fallback | Unset API key, analyse | Orange FALLBACK badge and note |

## Troubleshooting
- *Cannot reach the server*: check `VITE_API_URL` and that the backend allows your origin in `CORS_ORIGINS`.
- *Connection refused / password auth failed*: verify `DATABASE_URL` host/port/credentials (another Postgres may already use 5432).
- *Always FALLBACK*: key missing/invalid, quota exhausted or model name unavailable; check backend logs (`AI call failed`).
