# backend/services/watchdog.py
import numpy as np

def analyze_player_suspicion(player_id: int, db) -> dict:
    """
    Pega os últimos 20 logs do jogador e verifica se alguma métrica
    está além de 3 desvios padrão da média da tier dele.
    """
    
    # Busca stats históricas da tier/rank do jogador
    player_rating = db.query(PlayerRating).filter_by(player_id=player_id).first()
    tier_stats = get_tier_stats(player_rating.format, player_rating.elo)
    
    recent_logs = db.query(LogStats)\
        .filter_by(player_id=player_id)\
        .order_by(LogStats.date.desc())\
        .limit(20).all()
    
    flags = []
    
    # Métricas críticas por classe
    SUSPICIOUS_METRICS = {
        "sniper": ["headshots_pct", "dpm"],
        "soldier": ["airshots_per_game", "dpm"],
        "spy": ["backstabs_per_game", "kda"],
    }
    
    for class_name, metrics in SUSPICIOUS_METRICS.items():
        class_logs = [l for l in recent_logs if l.class_name == class_name]
        if len(class_logs) < 5:
            continue  # amostra insuficiente
        
        for metric in metrics:
            values = [getattr(l, metric, 0) for l in class_logs]
            tier_mean = tier_stats[class_name][metric]["mean"]
            tier_std  = tier_stats[class_name][metric]["std"]
            
            if tier_std == 0:
                continue
            
            player_mean = np.mean(values)
            z_score = (player_mean - tier_mean) / tier_std
            
            if z_score > 3.0:  # 99.7% da população está abaixo disso
                flags.append({
                    "metric": metric,
                    "class": class_name,
                    "z_score": round(z_score, 2),
                    "player_avg": round(player_mean, 1),
                    "tier_avg": round(tier_mean, 1),
                    "severity": "high" if z_score > 4 else "medium"
                })
    
    return {
        "player_id": player_id,
        "is_suspicious": len(flags) > 0,
        "flags": flags,
        "last_analyzed": datetime.now()
    }