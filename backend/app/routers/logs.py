# backend/app/routers/logs.py
import httpx
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import Player, LogEntry, PlayerClassAverage
from ..services.performance_score import calculate_performance_score

router = APIRouter()

LOGS_TF_API = "https://logs.tf/api/v1"


def _update_class_average(db: Session, player_id: int, log: LogEntry):
    """Recalcula a média incremental da classe após cada log importado."""
    if not log.class_played:
        return

    avg = db.query(PlayerClassAverage).filter_by(
        player_id=player_id,
        class_name=log.class_played,
        format=log.format
    ).first()

    if not avg:
        avg = PlayerClassAverage(
            player_id=player_id,
            class_name=log.class_played,
            format=log.format,
        )
        db.add(avg)

    n = avg.sample_size
    # Média incremental: nova_média = (média_antiga * n + novo_valor) / (n + 1)
    def inc(old, new):
        return (old * n + new) / (n + 1)

    avg.avg_dpm = inc(avg.avg_dpm, log.dpm)
    avg.avg_kda = inc(avg.avg_kda, log.kda)
    avg.avg_heals_per_min = inc(avg.avg_heals_per_min,
        log.heals_given / max(log.duration_seconds / 60, 1))
    avg.avg_ubers_per_game = inc(avg.avg_ubers_per_game, log.ubers)
    avg.avg_airshots = inc(avg.avg_airshots, log.airshots)
    avg.avg_headshots_pct = inc(avg.avg_headshots_pct, log.headshots_pct)
    avg.avg_backstabs = inc(avg.avg_backstabs, log.backstabs)
    avg.avg_captures = inc(avg.avg_captures, log.captures)
    avg.sample_size = n + 1

    db.commit()


@router.get("/import/{logs_tf_id}")
async def import_log(
    logs_tf_id: int,
    steam_id: str,
    format: Optional[str] = "6v6",
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Importa um log do logs.tf e calcula o Performance Score."""

    # Verifica se já foi importado
    existing = db.query(LogEntry).filter(LogEntry.logs_tf_id == logs_tf_id).first()
    if existing:
        return {"status": "already_imported", "log_id": existing.id}

    # Busca o jogador
    player = db.query(Player).filter(Player.steam_id == steam_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jogador não cadastrado. Crie o perfil primeiro.")

    # Busca o log na API do logs.tf
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{LOGS_TF_API}/log/{logs_tf_id}")
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="Log não encontrado no logs.tf")
        data = resp.json()

    # Extrai stats do jogador dentro do log
    player_data = data.get("players", {}).get(steam_id)
    if not player_data:
        raise HTTPException(status_code=404, detail="Steam ID não encontrado neste log")

    kills = player_data.get("kills", 0)
    deaths = player_data.get("deaths", 1)
    assists = player_data.get("assists", 0)
    kda = (kills + assists * 0.5) / max(deaths, 1)

    log = LogEntry(
        player_id=player.id,
        logs_tf_id=logs_tf_id,
        format=format,
        class_played=player_data.get("class"),
        dpm=player_data.get("dapm", 0),
        kills=kills,
        deaths=deaths,
        assists=assists,
        kda=round(kda, 2),
        heals_given=player_data.get("heal", 0),
        heals_received=player_data.get("hr", 0),
        ubers=player_data.get("ubers", 0),
        drops=player_data.get("drops", 0),
        airshots=player_data.get("as", 0),
        headshots=player_data.get("headshots", 0),
        headshots_pct=player_data.get("headshots_hit", 0),
        backstabs=player_data.get("backstabs", 0),
        captures=player_data.get("cpc", 0),
        duration_seconds=data.get("info", {}).get("total_length", 0),
    )

    db.add(log)
    db.flush()  # gera o ID sem commitar

    # Busca média histórica da classe para calcular Performance Score
    class_avg = db.query(PlayerClassAverage).filter_by(
        player_id=player.id,
        class_name=log.class_played,
        format=format
    ).first()

    if class_avg and class_avg.sample_size >= 3:
        avg_dict = {
            "avg_dpm": class_avg.avg_dpm,
            "avg_kda": class_avg.avg_kda,
            "avg_heals_per_min": class_avg.avg_heals_per_min,
            "avg_ubers": class_avg.avg_ubers_per_game,
            "avg_airshots": class_avg.avg_airshots,
            "avg_headshots_pct": class_avg.avg_headshots_pct,
            "avg_backstabs": class_avg.avg_backstabs,
            "avg_captures": class_avg.avg_captures,
        }
        log_stats = {
            "dpm": log.dpm, "kda": log.kda,
            "heals_per_min": log.heals_given / max(log.duration_seconds / 60, 1),
            "ubers": log.ubers, "airshots": log.airshots,
            "headshots_pct": log.headshots_pct,
            "backstabs": log.backstabs, "captures": log.captures,
        }
        log.performance_score = calculate_performance_score(
            log_stats, avg_dict, log.class_played or "default"
        )

    db.commit()

    # Atualiza médias em background (não bloqueia a resposta)
    if background_tasks:
        background_tasks.add_task(_update_class_average, db, player.id, log)

    score = log.performance_score
    score_label = ""
    if score is not None:
        if score > 10:
            score_label = f"🔥 +{score:.1f}% acima da sua média como {log.class_played}!"
        elif score < -10:
            score_label = f"📉 {score:.1f}% abaixo da sua média. Bora treinar!"
        else:
            score_label = f"➡️ Partida dentro da sua média habitual."

    return {
        "status": "imported",
        "logs_tf_id": logs_tf_id,
        "class": log.class_played,
        "dpm": log.dpm,
        "kda": log.kda,
        "performance_score": score,
        "performance_label": score_label,
        "format": format,
    }


@router.get("/player/{steam_id}")
def get_player_logs(
    steam_id: str,
    format: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Retorna os logs de um jogador, com Performance Score."""
    player = db.query(Player).filter(Player.steam_id == steam_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")

    query = db.query(LogEntry).filter(LogEntry.player_id == player.id)
    if format:
        query = query.filter(LogEntry.format == format)

    logs = query.order_by(LogEntry.created_at.desc()).limit(limit).all()

    return [
        {
            "logs_tf_id": l.logs_tf_id,
            "format": l.format,
            "class": l.class_played,
            "dpm": l.dpm,
            "kda": l.kda,
            "kills": l.kills,
            "deaths": l.deaths,
            "performance_score": l.performance_score,
            "result": l.result,
            "played_at": l.played_at,
        }
        for l in logs
    ]