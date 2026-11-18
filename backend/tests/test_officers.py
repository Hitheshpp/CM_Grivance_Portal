"""CMO officer-account management."""
from tests.conftest import login


def dept_id(client, code="PWD"):
    return next(d["id"] for d in client.get("/api/public/departments").json() if d["code"] == code)


def new_officer(client, cmo, **over):
    body = {"name": "Meera Das", "email": "meera.das@demo-portal.in", "mobile": "9876501234",
            "password": "TempPass1", "department_id": dept_id(client)}
    body.update(over)
    return client.post("/api/cmo/officers", json=body, headers=cmo)


def test_cmo_creates_officer_who_can_login_and_is_scoped(client, cmo, citizen):
    r = new_officer(client, cmo)
    assert r.status_code == 201 and r.json()["department"] == "Public Works Department"
    assert "password" not in str(r.json()).lower()
    h = login(client, "meera.das@demo-portal.in", "TempPass1")
    me = client.get("/api/auth/me", headers=h).json()
    assert me["role"] == "officer" and me["department"] == "Public Works Department"
    assert client.get("/api/cmo/stats", headers=h).status_code == 403  # officers cannot use CMO endpoints
    assert client.get("/api/grievances?page_size=100", headers=h).json()["total"] > 0


def test_create_officer_validation_and_permissions(client, cmo, citizen, officer_pwd):
    assert new_officer(client, cmo).status_code == 201
    assert new_officer(client, cmo).status_code == 409  # duplicate email
    assert new_officer(client, cmo, email="x@demo-portal.in", department_id=9999).status_code == 404
    assert new_officer(client, cmo, email="y@demo-portal.in", password="short").status_code == 422
    assert new_officer(client, cmo, email="z@demo-portal.in", mobile="123").status_code == 422
    body = {"name": "Eve Evil", "email": "eve@demo-portal.in", "mobile": "9876501234", "password": "TempPass1",
            "department_id": dept_id(client)}
    assert client.post("/api/cmo/officers", json=body, headers=citizen).status_code == 403
    assert client.post("/api/cmo/officers", json=body, headers=officer_pwd).status_code == 403
    assert client.post("/api/cmo/officers", json=body).status_code == 401


def test_deactivate_reactivate_and_reset_password(client, cmo):
    oid = new_officer(client, cmo).json()["id"]
    assert client.patch(f"/api/cmo/officers/{oid}/active", json={"is_active": False}, headers=cmo).status_code == 200
    r = client.post("/api/auth/login", json={"email": "meera.das@demo-portal.in", "password": "TempPass1"})
    assert r.status_code == 401
    # inactive officers are hidden from assignment dropdowns but visible to the management screen
    active_ids = [o["id"] for o in client.get("/api/cmo/officers", headers=cmo).json()]
    all_ids = [o["id"] for o in client.get("/api/cmo/officers?include_inactive=true", headers=cmo).json()]
    assert oid not in active_ids and oid in all_ids
    client.patch(f"/api/cmo/officers/{oid}/active", json={"is_active": True}, headers=cmo)
    r = client.post(f"/api/cmo/officers/{oid}/reset-password", json={"password": "NewPass99"}, headers=cmo)
    assert r.status_code == 200
    assert client.post("/api/auth/login", json={"email": "meera.das@demo-portal.in",
                                                "password": "TempPass1"}).status_code == 401
    login(client, "meera.das@demo-portal.in", "NewPass99")


def test_token_of_deactivated_officer_stops_working(client, cmo):
    oid = new_officer(client, cmo).json()["id"]
    h = login(client, "meera.das@demo-portal.in", "TempPass1")
    assert client.get("/api/auth/me", headers=h).status_code == 200
    client.patch(f"/api/cmo/officers/{oid}/active", json={"is_active": False}, headers=cmo)
    assert client.get("/api/auth/me", headers=h).status_code == 401


def test_cannot_manage_non_officer_accounts(client, cmo):
    # user id 1 is the CMO, citizens come after the officers; neither is manageable via this API
    assert client.patch("/api/cmo/officers/1/active", json={"is_active": False}, headers=cmo).status_code == 404
    assert client.post("/api/cmo/officers/1/reset-password", json={"password": "NewPass99"},
                       headers=cmo).status_code == 404
    assert client.get("/api/cmo/officers?include_inactive=true", headers=cmo).json()[0]["id"] != 1
