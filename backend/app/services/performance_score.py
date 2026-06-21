# backend/app/services/performance_score.py

WEIGHTS: dict[str, dict[str, float]] = {
    "soldier":  {"dpm": 0.5, "kda": 0.3, "airshots": 0.2},
    "medic":    {"heals_per_min": 0.6, "kda": 0.2, "ubers": 0.2},
    "scout":    {"dpm": 0.4, "kda": 0.4, "captures": 0.2},
    "sniper":   {"dpm": 0.3, "headshots_pct": 0.5, "kda": 0.2},
    "demoman":  {"dpm": 0.5, "kda": 0.3, "airshots": 0.2},
    "heavyweapons": {"dpm": 0.5, "kda": 0.5},
    "engineer": {"dpm": 0.4, "kda": 0.6},
    "spy":      {"kda": 0.5, "dpm": 0.3, "backstabs": 0.2},
    "pyro":     {"dpm": 0.6, "kda": 0.4},
    "default":  {"dpm": 0.5, "kda": 0.5},
}


def calculate_performance_score(
    log_stats: dict,
    class_avg: dict,
    class_name: str
) -> float:
    """
    Compara as stats da partida com a média histórica pessoal.
    Retorna um score de -100 a +100.
    +20 significa que o jogador jogou 20% acima da própria média.
    Requer mínimo de 3 partidas no histórico para ser confiável.
    """
    weights = WEIGHTS.get(class_name.lower(), WEIGHTS["default"])
    total_score = 0.0
    total_weight = 0.0

    for metric, weight in weights.items():
        current_val = log_stats.get(metric, 0) or 0
        avg_val = class_avg.get(f"avg_{metric}", 0) or 0

        if avg_val == 0:
            continue

        delta_pct = ((current_val - avg_val) / avg_val) * 100
        delta_pct = max(-100.0, min(100.0, delta_pct))

        total_score += delta_pct * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return round(total_score / total_weight, 1)