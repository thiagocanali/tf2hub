from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from .models import User, PlayerStats
from .services.logs_service import LogsService

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Ajuste para Codespaces: Permitir todas as origens
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/ranking")
async def get_ranking(db: Session = Depends(get_db)):
    from sqlalchemy import func
    results = db.query(
        PlayerStats.steam_id64,
        func.avg(PlayerStats.dpm).label("avg_dpm")
    ).group_by(PlayerStats.steam_id64).order_by(func.avg(PlayerStats.dpm).desc()).limit(10).all()
    return [{"steam_id": r[0], "dpm": round(r[1], 2)} for r in results]

@app.get("/api/players/{steamid}")
async def get_player(steamid: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.steam_id64 == steamid).first()
    if not user:
        user = User(steam_id64=steamid, username=f"Player_{steamid[-4:]}")
        db.add(user)
        db.commit()
        db.refresh(user)
    stats = db.query(PlayerStats).filter(PlayerStats.steam_id64 == steamid).all()
    return {"user": user, "stats": stats}

@app.post("/api/sync/{steamid}")
async def sync_data(steamid: str, db: Session = Depends(get_db)):
    success = await LogsService.sync_player_logs(steamid, db)
    return {"status": "success" if success else "failed"}