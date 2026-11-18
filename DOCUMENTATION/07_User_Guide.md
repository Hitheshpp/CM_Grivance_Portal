# 07 – User Guide

> Recruitment prototype with fictional data – see the banner on every page. Demo accounts: [06_Setup_and_Testing.md](06_Setup_and_Testing.md).

## Public visitors
- **Home** – introduction, *Submit Grievance* and *Track Grievance* buttons, sample statistics, featured departments.
- **About Us / How It Works / Departments / FAQ** – information pages.
- **Contact Us** – send an enquiry (stored in the database; CMO can read it).
- **Track** – enter a reference number (e.g. `KGR-2026-000012`) to see status, department and public updates.

## Citizens
1. **Register** (name, email, 10-digit mobile, password with letters and digits) or **Login**. Use *Logout* in the menu when done.
2. **Submit grievance** (*My Dashboard → Submit new grievance*):
   - choose district and category, write a subject and a detailed description;
   - click **Analyse my description** to get the AI suggestion (category, priority, department, summary, possible duplicates).
     Review it, then click *Use suggested category & priority* or ignore it – you decide;
   - optionally attach a PDF/JPG/PNG/WEBP (max 5 MB) and submit.
3. **Save your reference number** shown after submission.
4. **Dashboard** shows total / pending / resolved / overdue counts and your grievances (filter by status).
5. **Open a grievance** to see current status, assigned department, officer/CMO remarks and the complete status history.
6. **After resolution:** read the action-taken report, **rate** the outcome (once), or **Reopen** with a reason if the issue persists.

## CMO administrators
1. **Login** with the CMO account → *CMO Dashboard*.
2. **Overview & statistics:** total, pending, resolved, overdue, escalated and reports awaiting review (click a tile to filter);
   charts for district-wise grievances, status distribution, categories and department-wise resolved vs overdue; a department table.
3. **All grievances:** filter by district, category, priority, status, overdue or search; open any record.
4. **Inside a grievance:**
   - review the complaint, attachments and the **AI suggestion** (labelled AI or FALLBACK, with duplicates);
   - **Confirm / save triage** to accept or override category and priority;
   - **Forward to department** (and optionally a specific officer) – status becomes *Under Review*;
   - **Add remark** as *internal* (CMO only), *department*, or *public* (visible to the citizen);
   - **Escalate** delayed grievances (sets High priority and flags it to the department);
   - when a department has submitted its action-taken report, **Accept & resolve** or **Return** with remarks.
5. **Manage officers** tab: create officer accounts (name, email, mobile, department, temporary password), deactivate/reactivate
   officers, or reset a password. Share temporary passwords through a secure channel.
6. **Contact enquiries** tab lists messages from the Contact form.

## Department officers
1. **Login** with an officer account – the dashboard lists only your department's grievances with counts.
2. Open a grievance to read details and attachments.
3. **Mark In Progress** when work starts; add **investigation remarks** (visible to the citizen or to CMO/department only).
4. When done, write the **action-taken report** (optionally attach a document) and **Submit to CMO for review**.
5. If the CMO returns the report, the grievance goes back to *In Progress* – read the remarks and resubmit.
6. Officers cannot mark grievances *Resolved*; only the CMO's acceptance does.

## Status meanings
| Status | Meaning |
|---|---|
| Submitted | Received; awaiting CMO review |
| Under Review | CMO reviewing/forwarded to a department |
| In Progress | Department is acting |
| Resolved | CMO accepted the action-taken report |
| Reopened | Citizen reported the problem persists |

Overdue = not resolved and past its target date (High 7 days, Medium 15 days, Low 30 days from submission).
