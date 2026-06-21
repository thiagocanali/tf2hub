# backend/app/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://tf2user:tf2pass@db:5432/tf2hub"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Cria todas as tabelas se não existirem. Chamado no startup da app."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency do FastAPI para injetar sessão do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()