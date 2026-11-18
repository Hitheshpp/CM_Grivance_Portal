# CM Kerala – Chief Minister's Public Grievance Redressal Portal (Recruitment Prototype)

> **Disclaimer:** This is a **recruitment-assessment prototype** built for the WhiteMatrix "AI Full Stack Engineer" machine test.
> It is **not** an official website and is **not** affiliated with, authorised or endorsed by the Government of Kerala or the
> Chief Minister's Office. All users, departments and grievances are **fictional**. Do not enter real personal data.

A working end-to-end grievance workflow: **citizen submits → reference ID → CMO reviews → forwards to department → officer
investigates → action-taken report → CMO reviews → citizen notified → Resolved / Reopened**, with an AI triage assistant.

## Links
| | |
|---|---|
| Hosted application | _add URL after deployment_ |
| Hosted API docs | _add URL_`/docs` |
| Demo video | _add URL_ |

## Demo credentials (fictional test accounts)
Password for all: **`Demo@1234`**

| Role | Email |
|---|---|
| CMO admin | `cmo@demo-portal.in` |
| Citizen | `citizen1@demo-portal.in` (… up to `citizen5@`) |
| Officer – Public Works | `officer.pwd@demo-portal.in` |
| Officer – Health | `officer.health@demo-portal.in` |
| Other officers | `officer.<edu|water|power|lsgd|home|sjd|agri|env>@demo-portal.in` |

## Tech stack
React 18 + Vite + Recharts · **FastAPI** (Python 3.12) + SQLAlchemy 2 · **PostgreSQL** · JWT (RBAC: citizen / cmo / officer) ·
LLM: OpenAI, Anthropic Claude or Google Gemini (configurable) (with clearly labelled fallback).

## Repository structure
```
backend/            FastAPI app (app/routers, app/services, models, seed) + tests/
frontend/           React SPA (src/pages, components, api client)
DOCUMENTATION/      01–07 mandatory docs + diagrams/ (architecture, ER)
.env.example        Environment template (no secrets)
```

## Quick start
```bash
# 1. PostgreSQL – create a database named cmgrp (see DOCUMENTATION/06_Setup_and_Testing.md)
# 2. Backend
cd backend && python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env          # set DATABASE_URL, JWT_SECRET, optional AI key
uvicorn app.main:app --reload --port 8001
# 3. Frontend
cd ../frontend && npm install && echo "VITE_API_URL=http://localhost:8001" > .env && npm run dev
```
Open http://localhost:5173. Demo data is seeded automatically on first start. Full instructions: [06_Setup_and_Testing](DOCUMENTATION/06_Setup_and_Testing.md).

## Tests
`cd backend && pytest -q` → 17 end-to-end API tests (RBAC, full workflow, AI fallback, uploads, statistics).

## Documentation
1. [Project Overview](DOCUMENTATION/01_Project_Overview.md) · 2. [System Architecture](DOCUMENTATION/02_System_Architecture.md) ·
3. [Database Design](DOCUMENTATION/03_Database_Design.md) · 4. [API Documentation](DOCUMENTATION/04_API_Documentation.md) ·
5. [AI Integration](DOCUMENTATION/05_AI_Integration.md) · 6. [Setup & Testing](DOCUMENTATION/06_Setup_and_Testing.md) ·
7. [User Guide](DOCUMENTATION/07_User_Guide.md)
Diagrams: [Architecture](DOCUMENTATION/diagrams/system_architecture.md) · [ER diagram](DOCUMENTATION/diagrams/er_diagram.md)

## AI integration (summary)
`POST /api/ai/analyze` sends the complaint to a real LLM and returns suggested department, category, priority, a CMO summary and
possible duplicates. Output is validated against allow-lists, shown to the citizen for review and to the CMO for confirmation; the
AI never makes official decisions. Without a key it falls back to a keyword classifier that is **explicitly labelled** in the UI/API.
Details and limitations: [05_AI_Integration](DOCUMENTATION/05_AI_Integration.md).

## Tools and third-party services disclosed
Claude Code (AI coding assistant) · OpenAI / Anthropic / Google Gemini LLM APIs (runtime, optional) · open-source libraries listed in
`backend/requirements.txt` and `frontend/package.json` · hosting providers as listed above.

## Known limitations (prototype)
No email/SMS (updates are in-app) · no password reset · officer accounts are seeded (no admin UI) · tables auto-created (no Alembic
migrations) · in-memory rate limiter (single instance) · JWT in localStorage · files stored in PostgreSQL (5 MB limit).
