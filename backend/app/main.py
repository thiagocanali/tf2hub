# backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import create_tables, get_db
from .models import Player, PlayerRating, PlayerClassAverage, LogEntry, WatchdogFlag
from .routers import players, logs, watchdog

app = FastAPI(title="TF2Hub API", version="2.0.0")

# CORS — libera o frontend (Docker interno + Codespaces)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em prod, trocar pelo domínio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria as tabelas no banco na inicialização
@app.on_event("startup")
def on_startup():
    create_tables()

# Routers
app.include_router(players.router, prefix="/players", tags=["players"])
app.include_router(logs.router, prefix="/logs", tags=["logs"])
app.include_router(watchdog.router, prefix="/watchdog", tags=["watchdog"])


@app.get("/")
def read_root():
    return {"status": "TF2Hub API v2 online!", "docs": "/docs"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB error: {str(e)}")