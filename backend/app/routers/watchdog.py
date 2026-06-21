# backend/app/routers/watchdog.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import numpy as np

from ..database import get_db
from ..models import Player, LogEntry, PlayerRating, WatchdogFlag

router = APIRouter()

# Médias de referência por tier (ELO) e classe
# Estes valores devem ser calibrados com dados reais da comunidade BR
TIER_BASELINES = {
    "sniper": {
        "headshots_pct": {"open": (30, 10), "invite": (55, 8)},
        "dpm":           {"open": (180, 40), "invite": (260, 35)},
    },
    "soldier": {
        "airshots":      {"open": (1.5, 1.2), "invite": (4.0, 2.0)},
        "dpm":           {"open": (200, 45), "invite": (310, 40)},
    },
    "spy": {
        "backstabs":     {"open": (1.0, 0.8), "invite": (2.5, 1.2)},
        "kda":           {"open": (1.2, 0.5), "invite": (2.0, 0.7)},
    },
}


def _get_tier(elo: int) -> str:
    if elo >= 1400:
        return "invite"
    return "open"


@router.get("/analyze/{steam_id}")
def analyze_player(steam_id: str, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.steam_id == steam_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    # Pega o rating no formato mais jogado
    rating = db.query(PlayerRating).filter_by(player_id=player.id).order_by(
        PlayerRating.games_played.desc()
    ).first()

    tier = _get_tier(rating.elo if rating else 1000)

    recent_logs = db.query(LogEntry).filter_by(player_id=player.id)\
        .order_by(LogEntry.created_at.desc()).limit(20).all()

    if len(recent_logs) < 5:
        return {
            "steam_id": steam_id,
            "is_suspicious": False,
            "reason": "Amostra insuficiente (mínimo 5 logs)",
            "flags": []
        }

    new_flags = []

    for class_name, metrics in TIER_BASELINES.items():
        class_logs = [l for l in recent_logs if l.class_played == class_name]
        if len(class_logs) < 3:
            continue

        for metric, tiers in metrics.items():
            values = [getattr(l, metric, 0) or 0 for l in class_logs]
            tier_mean, tier_std = tiers.get(tier, tiers["open"])

            if tier_std == 0:
                continue

            player_mean = float(np.mean(values))
            z_score = (player_mean - tier_mean) / tier_std

            if z_score > 3.0:
                severity = "high" if z_score > 4.0 else "medium"

                # Salva a flag no banco (evita duplicatas)
                existing = db.query(WatchdogFlag).filter_by(
                    player_id=player.id,
                    metric=metric,
                    class_name=class_name,
                    resolved=False
                ).first()

                if not existing:
                    flag = WatchdogFlag(
                        player_id=player.id,
                        metric=metric,
                        class_name=class_name,
                        z_score=round(z_score, 2),
                        player_avg=round(player_mean, 1),
                        tier_avg=round(tier_mean, 1),
                        severity=severity,
                    )
                    db.add(flag)
                    new_flags.append(flag)

    db.commit()

    all_flags = db.query(WatchdogFlag).filter_by(
        player_id=player.id, resolved=False
    ).all()

    return {
        "steam_id": steam_id,
        "tier": tier,
        "elo": rating.elo if rating else 1000,
        "is_suspicious": len(all_flags) > 0,
        "flags": [
            {
                "metric": f.metric,
                "class": f.class_name,
                "z_score": f.z_score,
                "player_avg": f.player_avg,
                "tier_avg": f.tier_avg,
                "severity": f.severity,
            }
            for f in all_flags
        ],
        "new_flags_found": len(new_flags),
    }