"""End-to-end API tests covering auth, RBAC, the full grievance workflow, AI fallback and uploads."""
from tests.conftest import login

PDF = b"%PDF-1.4 fake pdf content for testing"
DESC = ("There is a very large pothole on the main road near the bus stand. It is dangerous for school "
        "children and two wheelers, please repair the road urgently.")


def submit(client, headers, **over):
    with_file = over.pop("with_file", False)
    data = {"district": "Ernakulam", "category": "Roads & Infrastructure", "subject": "Pothole near bus stand",
            "description": DESC}
    data.update(over)
    files = {"file": ("evidence.pdf", PDF, "application/pdf")} if with_file else None
    return client.post("/api/grievances", data=data, headers=headers, files=files)


# ------------------------------------------------------------------ auth
def test_register_login_and_me(client):
    r = client.post("/api/auth/register", json={"name": "Test User", "email": "new@demo-portal.in",
                                                "mobile": "9876543210", "password": "Passw0rdX"})
    assert r.status_code == 201 and r.json()["user"]["role"] == "citizen"
    h = login(client, "new@demo-portal.in", "Passw0rdX")
    assert client.get("/api/auth/me", headers=h).json()["email"] == "new@demo-portal.in"


def test_register_validation_and_duplicates(client):
    bad = {"name": "X Y", "email": "a@demo-portal.in", "mobile": "12345", "password": "Passw0rdX"}
    assert client.post("/api/auth/register", json=bad).status_code == 422
    assert client.post("/api/auth/register", json={**bad, "mobile": "9876543210", "password": "short"}).status_code == 422
    dup = {**bad, "email": "citizen1@demo-portal.in", "mobile": "9876543210"}
    assert client.post("/api/auth/register", json=dup).status_code == 409


def test_register_cannot_choose_role(client):
    r = client.post("/api/auth/register", json={"name": "Sneaky", "email": "s@demo-portal.in", "mobile": "9876543210",
                                                "password": "Passw0rdX", "role": "cmo"})
    assert r.json()["user"]["role"] == "citizen"


def test_login_failure_is_generic(client):
    r1 = client.post("/api/auth/login", json={"email": "nobody@demo-portal.in", "password": "x"})
    r2 = client.post("/api/auth/login", json={"email": "citizen1@demo-portal.in", "password": "wrong"})
    assert r1.status_code == r2.status_code == 401 and r1.json() == r2.json()


def test_login_rate_limit(client):
    codes = [client.post("/api/auth/login", json={"email": "x@y.in", "password": "x"}).status_code for _ in range(12)]
    assert 429 in codes


def test_protected_routes_need_token_and_role(client, citizen, officer_pwd):
    assert client.get("/api/grievances").status_code == 401
    assert client.get("/api/cmo/stats", headers=citizen).status_code == 403
    assert client.get("/api/cmo/stats", headers=officer_pwd).status_code == 403
    assert client.get("/api/cmo/stats", headers={"Authorization": "Bearer garbage"}).status_code == 401


# ------------------------------------------------------------------ public
def test_public_endpoints(client):
    assert len(client.get("/api/public/departments").json()) == 10
    assert client.get("/api/public/stats").json()["total_grievances"] > 0
    r = client.post("/api/public/contact", json={"name": "Ann", "email": "ann@demo-portal.in",
                                                 "subject": "Question", "message": "How long does it take?"})
    assert r.status_code == 201


def test_public_track_hides_private_data(client, citizen):
    ref = submit(client, citizen).json()["reference_no"]
    t = client.get(f"/api/public/track/{ref}").json()
    assert t["status"] == "Submitted" and "description" not in t and "citizen" not in t
    assert client.get("/api/public/track/KGR-0000-999999").status_code == 404


# ------------------------------------------------------------------ AI
def test_ai_analyze_uses_labelled_fallback_without_key(client, citizen):
    r = client.post("/api/ai/analyze", json={"description": DESC, "subject": "Pothole", "district": "Ernakulam"},
                    headers=citizen)
    body = r.json()
    assert r.status_code == 200
    assert body["is_fallback"] is True and body["provider"] == "keyword-fallback"
    assert body["category"] == "Roads & Infrastructure" and body["priority"] in ("Low", "Medium", "High")
    assert body["summary"] and "not an official decision" in body["disclaimer"]


def test_ai_requires_auth_and_valid_input(client, citizen):
    assert client.post("/api/ai/analyze", json={"description": DESC}).status_code == 401
    assert client.post("/api/ai/analyze", json={"description": "short"}, headers=citizen).status_code == 422


def test_duplicate_detection(client, citizen):
    submit(client, citizen)
    r = client.post("/api/ai/analyze", json={"description": DESC, "subject": "Pothole near bus stand",
                                             "district": "Ernakulam"}, headers=citizen)
    assert r.json()["duplicates"], "identical complaint should be flagged as a possible duplicate"


# ------------------------------------------------------------------ full workflow
def test_full_lifecycle(client, citizen, cmo, officer_pwd):
    # 1. citizen submits (with attachment) -> reference id + history
    r = submit(client, citizen, with_file=True)
    assert r.status_code == 201, r.text
    ref = r.json()["reference_no"]
    assert ref.startswith("KGR-")

    # 2. CMO sees it, reviews AI triage, forwards to PWD
    assert client.get(f"/api/grievances/{ref}", headers=cmo).json()["ai"]["notice"]
    r = client.patch(f"/api/cmo/grievances/{ref}/triage", json={"priority": "High"}, headers=cmo)
    assert r.json()["priority"] == "High"
    pwd_id = next(d["id"] for d in client.get("/api/public/departments").json() if d["code"] == "PWD")
    r = client.post(f"/api/cmo/grievances/{ref}/assign", json={"department_id": pwd_id}, headers=cmo)
    assert r.status_code == 200 and r.json()["status"] == "Under Review" and r.json()["department"]

    # 3. officer can now see it and an unrelated officer cannot
    assert client.get(f"/api/grievances/{ref}", headers=officer_pwd).status_code == 200
    other = login(client, "officer.edu@demo-portal.in")
    assert client.get(f"/api/grievances/{ref}", headers=other).status_code == 404

    # officer cannot jump straight to Resolved, nor submit a report before In Progress
    assert client.patch(f"/api/grievances/{ref}/status", json={"status": "Resolved"},
                        headers=officer_pwd).status_code == 400
    rep = {"report_text": "Repaired the road surface and inspected the site thoroughly."}
    assert client.post(f"/api/officer/grievances/{ref}/report", data=rep, headers=officer_pwd).status_code == 400

    # 4. officer investigates
    r = client.patch(f"/api/grievances/{ref}/status", json={"status": "In Progress", "remarks": "Work started"},
                     headers=officer_pwd)
    assert r.status_code == 200 and r.json()["status"] == "In Progress"
    r = client.post(f"/api/grievances/{ref}/remarks", json={"remarks": "Contractor engaged", "visibility": "internal"},
                    headers=officer_pwd)
    assert r.status_code == 403  # officers cannot write CMO-internal remarks

    # 5. action-taken report -> pending CMO review; citizen does not see it yet
    r = client.post(f"/api/officer/grievances/{ref}/report", data=rep, headers=officer_pwd)
    assert r.status_code == 200 and r.json()["report_status"] == "Pending CMO Review"
    assert client.get(f"/api/grievances/{ref}", headers=citizen).json()["action_taken_report"] is None

    # 6. CMO rejects once, officer resubmits, CMO accepts
    assert client.post(f"/api/cmo/grievances/{ref}/review-report", json={"decision": "reject"},
                       headers=cmo).status_code == 400  # remarks required
    r = client.post(f"/api/cmo/grievances/{ref}/review-report",
                    json={"decision": "reject", "remarks": "Need photos"}, headers=cmo)
    assert r.json()["status"] == "In Progress"
    client.post(f"/api/officer/grievances/{ref}/report", data=rep, headers=officer_pwd)
    r = client.post(f"/api/cmo/grievances/{ref}/review-report", json={"decision": "accept"}, headers=cmo)
    assert r.json()["status"] == "Resolved"

    # 7. citizen sees the resolution, gives feedback once, can reopen
    d = client.get(f"/api/grievances/{ref}", headers=citizen).json()
    assert d["status"] == "Resolved" and d["action_taken_report"] and d["can_give_feedback"]
    assert client.post(f"/api/grievances/{ref}/feedback", json={"rating": 5, "comment": "Great"},
                       headers=citizen).status_code == 201
    assert client.post(f"/api/grievances/{ref}/feedback", json={"rating": 1}, headers=citizen).status_code == 400
    r = client.patch(f"/api/grievances/{ref}/status", json={"status": "Reopened"}, headers=citizen)
    assert r.status_code == 400  # reason required
    r = client.patch(f"/api/grievances/{ref}/status", json={"status": "Reopened", "remarks": "Hole is back"},
                     headers=citizen)
    assert r.json()["status"] == "Reopened"

    # 8. audit trail is complete, ordered, attributed; citizen never sees internal/department notes
    cmo_view = client.get(f"/api/grievances/{ref}", headers=cmo).json()
    actions = [h["action"] for h in cmo_view["history"]]
    assert actions[0] == "Grievance submitted" and "Resolved: report accepted by CMO" in actions
    assert all(h["actor_name"] for h in cmo_view["history"])
    citizen_view = client.get(f"/api/grievances/{ref}", headers=citizen).json()
    assert all("visibility" not in h for h in citizen_view["history"])
    assert "CMO reviewed AI triage" not in [h["action"] for h in citizen_view["history"]]


def test_attachment_download_and_access(client, citizen, cmo):
    ref = submit(client, citizen, with_file=True).json()["reference_no"]
    att = client.get(f"/api/grievances/{ref}", headers=citizen).json()["attachments"][0]
    r = client.get(f"/api/grievances/{ref}/attachments/{att['id']}", headers=cmo)
    assert r.status_code == 200 and r.content == PDF and r.headers["x-content-type-options"] == "nosniff"
    stranger = login(client, "citizen2@demo-portal.in")
    assert client.get(f"/api/grievances/{ref}/attachments/{att['id']}", headers=stranger).status_code == 404


def test_upload_validation(client, citizen):
    base = {"district": "Kollam", "category": "Healthcare", "subject": "Clinic issue", "description": DESC}
    bad_type = client.post("/api/grievances", data=base, headers=citizen,
                           files={"file": ("x.exe", b"MZ....", "application/x-msdownload")})
    assert bad_type.status_code == 415
    spoofed = client.post("/api/grievances", data=base, headers=citizen,
                          files={"file": ("x.pdf", b"not a pdf at all", "application/pdf")})
    assert spoofed.status_code == 415
    big = client.post("/api/grievances", data=base, headers=citizen,
                      files={"file": ("x.pdf", b"%PDF" + b"0" * (6 * 1024 * 1024), "application/pdf")})
    assert big.status_code == 413


# ------------------------------------------------------------------ isolation & CMO views
def test_citizens_only_see_own_grievances(client, citizen):
    mine = client.get("/api/grievances", headers=citizen).json()
    assert mine["total"] > 0
    other = login(client, "citizen2@demo-portal.in")
    ref = mine["items"][0]["reference_no"]
    assert client.get(f"/api/grievances/{ref}", headers=other).status_code == 404


def test_cmo_list_filters_and_stats(client, cmo):
    allg = client.get("/api/grievances?page_size=100", headers=cmo).json()
    assert allg["total"] >= 30
    res = client.get("/api/grievances?status=Resolved&page_size=100", headers=cmo).json()
    assert res["total"] > 0 and all(i["status"] == "Resolved" for i in res["items"])
    od = client.get("/api/grievances?overdue=true&page_size=100", headers=cmo).json()
    assert all(i["overdue"] for i in od["items"])
    s = client.get("/api/cmo/stats", headers=cmo).json()
    assert s["total"] == allg["total"] and s["pending"] + s["resolved"] == s["total"]
    assert s["by_district"] and s["by_department"] and s["overdue"] == od["total"]


def test_escalation_and_assign_validation(client, citizen, cmo):
    ref = submit(client, citizen).json()["reference_no"]
    r = client.post(f"/api/cmo/grievances/{ref}/escalate", json={"reason": "Delayed beyond SLA"}, headers=cmo)
    assert r.json()["escalated"] is True and r.json()["priority"] == "High"
    depts = {d["code"]: d["id"] for d in client.get("/api/public/departments").json()}
    officers = client.get("/api/cmo/officers", headers=cmo).json()
    edu_officer = next(o for o in officers if o["department"] == "General Education")
    bad = client.post(f"/api/cmo/grievances/{ref}/assign",
                      json={"department_id": depts["PWD"], "officer_id": edu_officer["id"]}, headers=cmo)
    assert bad.status_code == 400
