# backend/app/routers/players.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..database import get_db
from ..models import Player, PlayerRating

router = APIRouter()


class PlayerCreate(BaseModel):
    steam_id: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class DiscordLink(BaseModel):
    discord_id: str
    discord_username: str


@router.get("/{steam_id}")
def get_player(steam_id: str, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.steam_id == steam_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    ratings = {r.format: {"elo": r.elo, "peak": r.peak_elo, "games": r.games_played}
               for r in player.ratings}

    return {
        "steam_id": player.steam_id,
        "display_name": player.display_name,
        "avatar_url": player.avatar_url,
        "discord_linked": player.discord_id is not None,
        "ratings": ratings,
        "member_since": player.created_at,
    }


@router.post("/")
def create_or_update_player(data: PlayerCreate, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.steam_id == data.steam_id).first()
    if not player:
        player = Player(
            steam_id=data.steam_id,
            display_name=data.display_name,
            avatar_url=data.avatar_url,
        )
        db.add(player)
        db.commit()
        db.refresh(player)
        # Cria ratings padrão para todos os formatos
        for fmt in ["6v6", "highlander", "4v4", "mix"]:
            db.add(PlayerRating(player_id=player.id, format=fmt))
        db.commit()
    else:
        if data.display_name:
            player.display_name = data.display_name
        if data.avatar_url:
            player.avatar_url = data.avatar_url
        db.commit()

    return {"id": player.id, "steam_id": player.steam_id}


@router.post("/link-discord")
def link_discord(data: DiscordLink, steam_id: str, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.steam_id == steam_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    player.discord_id = data.discord_id
    db.commit()
    return {"linked": True, "discord_id": data.discord_id}