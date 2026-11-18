import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, text

from .config import get_settings
from .database import Base, SessionLocal, engine
from .models import User
from .routers import ai, auth, cmo, grievances, officer, public

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    if get_settings().seed_on_startup:
        from .seed import seed
        with SessionLocal() as db:
            if not db.scalar(select(func.count(User.id))):
                seed(db)
    yield


app = FastAPI(
    title=get_settings().app_name, version="1.0.0", lifespan=lifespan,
    description="REST API for a recruitment-assessment prototype. NOT affiliated with or endorsed by the "
                "Government of Kerala or the Chief Minister's Office. All data is fictional.")

app.add_middleware(
    CORSMiddleware, allow_origins=get_settings().cors_origin_list, allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["Authorization", "Content-Type"])


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    return response


for r in (public.router, auth.router, grievances.router, ai.router, cmo.router, officer.router):
    app.include_router(r)


@app.get("/api/health", tags=["Health"])
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
