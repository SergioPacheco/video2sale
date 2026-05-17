from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


def get_engine():
    return create_engine(settings.database_url)


def get_session_local():
    return sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)


def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
