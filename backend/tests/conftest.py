import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite://"
os.environ["AI_PROVIDER"] = "none"  # tests must never call a paid API -> exercises the labelled fallback
os.environ["SEED_ON_STARTUP"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.routers import ai, auth, grievances, public  # noqa: E402
from app.seed import DEMO_PASSWORD, seed  # noqa: E402


@pytest.fixture()
def client():
    engine = create_engine("sqlite+pysqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Session() as s:
        seed(s)

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    # reset in-memory rate limiters between tests
    for limiter in (auth.login_limit, auth.register_limit, grievances.submit_limit, ai.ai_limit,
                    public.contact_limit, public.track_limit):
        limiter.hits.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()


def login(client, email, password=DEMO_PASSWORD):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def citizen(client):
    return login(client, "citizen1@demo-portal.in")


@pytest.fixture()
def cmo(client):
    return login(client, "cmo@demo-portal.in")


@pytest.fixture()
def officer_pwd(client):
    return login(client, "officer.pwd@demo-portal.in")
