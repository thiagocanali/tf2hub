# backend/services/performance_score.py

def calculate_performance_score(
    log_stats: dict,        # stats da partida atual
    class_avg: dict,        # média histórica da tabela player_class_averages
    class_name: str
) -> float:
    """
    Retorna um score de -100 a +100.
    +20 = jogou 20% acima da média pessoal.
    """
    
    # Pesos por classe — DPM importa mais pro Soldier, heals pro Medic
    WEIGHTS = {
        "soldier":  {"dpm": 0.5, "kda": 0.3, "airshots": 0.2},
        "medic":    {"heals_per_min": 0.6, "kda": 0.2, "ubers": 0.2},
        "scout":    {"dpm": 0.4, "kda": 0.4, "captures": 0.2},
        "sniper":   {"dpm": 0.3, "headshots_pct": 0.5, "kda": 0.2},
        "demo":     {"dpm": 0.5, "kda": 0.3, "airshots": 0.2},
        "heavy":    {"dpm": 0.5, "kda": 0.4, "damage_taken_ratio": 0.1},
        "engineer": {"dpm": 0.3, "kda": 0.3, "buildings_built": 0.4},
        "spy":      {"kda": 0.5, "dpm": 0.3, "backstabs": 0.2},
        "pyro":     {"dpm": 0.5, "kda": 0.4, "afterburn_kills": 0.1},
        "default":  {"dpm": 0.5, "kda": 0.5},
    }
    
    weights = WEIGHTS.get(class_name.lower(), WEIGHTS["default"])
    total_score = 0.0
    total_weight = 0.0
    
    for metric, weight in weights.items():
        current_val = log_stats.get(metric, 0)
        avg_val = class_avg.get(f"avg_{metric}", 0)
        
        if avg_val == 0:
            continue  # sem histórico ainda, não penaliza
        
        # Delta percentual em relação à média pessoal
        delta_pct = ((current_val - avg_val) / avg_val) * 100
        # Limita a ±100% para não explodir o score
        delta_pct = max(-100, min(100, delta_pct))
        
        total_score += delta_pct * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return round(total_score / total_weight, 1)