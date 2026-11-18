from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings


def normalize_db_url(url: str) -> str:
    """Hosts such as Render/Heroku give postgres:// URLs; SQLAlchemy needs the psycopg driver."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


class Base(DeclarativeBase):
    pass


_url = normalize_db_url(get_settings().database_url)
# prepare_threshold=None disables server-side prepared statements, which break behind PgBouncer
# poolers (e.g. Neon's "-pooler" hosts). Negligible cost at this scale.
_connect_args = {"prepare_threshold": None} if _url.startswith("postgresql") else {}
engine = create_engine(_url, pool_pre_ping=True, pool_recycle=300, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
