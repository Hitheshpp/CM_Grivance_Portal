# 01 – Project Overview

> **Recruitment prototype.** Built for the WhiteMatrix "AI Full Stack Engineer" machine test. It is **not** an official
> website and is **not** affiliated with or endorsed by the Government of Kerala or the Chief Minister's Office.
> All users, departments and grievances are fictional.

## Problem statement
Citizens face problems with public infrastructure, healthcare, education and services, but have no single accountable channel
to report them, see who is acting, and learn the outcome. The Chief Minister's Office (CMO) needs to triage grievances, route
them to the right department, watch for delays and verify that action was really taken.

## Objectives
1. One online window to submit grievances and receive a unique reference number.
2. Traceable lifecycle: every status change stored with timestamp and responsible user.
3. CMO control: review, assign, escalate, and approve action-taken reports before closure.
4. Department accountability: officers see only their department's grievances and must report back.
5. Citizen closure: visible updates, feedback after resolution, and the ability to reopen.
6. Responsible AI: advisory triage (department, category, priority, summary, duplicates) that humans review.

## Scope
**In scope:** public website, citizen portal, CMO dashboard, officer dashboard, AI assistant, file upload/retrieval,
role-based access, statistics, documentation.
**Out of scope (prototype limits):** real e-mail/SMS notifications (updates are shown in-app), Malayalam localisation,
password reset, admin UI for creating officer accounts (seeded), virus scanning, multi-instance rate limiting, database
migrations tooling (tables are created on start).

## Features by role
| Role | Capabilities |
|---|---|
| Visitor | Home, About, How It Works, Departments, FAQ, Contact form (saved to DB), public tracking by reference number |
| Citizen | Register/login/logout, submit grievance with optional file, AI assistant with review, dashboard (total/pending/resolved/overdue), grievance details with timeline, feedback after resolution, reopen with reason |
| CMO admin | All grievances; total/pending/resolved/overdue; filters (district, category, priority, status, overdue, search); view attachments; confirm/override AI triage; forward/reassign to department & officer; internal/department/public remarks; escalate; review action-taken reports (accept → Resolved, or return); district-wise and department-wise charts and tables; contact enquiries |
| Department officer | Login; see only own department's grievances; view details/attachments; set In Progress; add remarks; submit action-taken report (text + optional file) |

## Workflow
Citizen submits → system generates reference ID → CMO reviews → CMO forwards to department → officer investigates and
updates progress → department submits action-taken report → CMO reviews response → citizen receives update →
**Resolved** or **Reopened**. Statuses: `Submitted`, `Under Review`, `In Progress`, `Resolved`, `Reopened`.

## Technology
React 18 + Vite · FastAPI (Python 3.12) · SQLAlchemy 2 · PostgreSQL · JWT · Anthropic Claude / Google Gemini (LLM) ·
Recharts. See [02_System_Architecture.md](02_System_Architecture.md).

## Tools and third-party services disclosed
- **AI coding assistant:** Claude Code (Anthropic) was used to help write and review code and documentation.
- **LLM API at runtime:** Anthropic Messages API or Google Gemini API (configurable; optional).
- **Open-source libraries:** FastAPI, Uvicorn, SQLAlchemy, Pydantic, PyJWT, bcrypt, httpx, pytest, React, React Router, Recharts, Vite.
- **Hosting/DB:** see the README for the deployed environment.
