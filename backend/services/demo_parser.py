# backend/services/demo_parser.py
# Usa a lib 'demoparser2' (Rust-based, rápida)

from demoparser2 import DemoParser

def extract_highlights(demo_path: str) -> list[dict]:
    """
    Identifica momentos 'hype' no demo:
    - Airshots: projétil no ar por >0.5s que acerta player airborne
    - Medic picks: kill num medic com uber disponível  
    - Backcaps: captura de ponto vindo de trás das linhas
    """
    parser = DemoParser(demo_path)
    
    kills = parser.parse_event("player_death", 
        player=["X", "Y", "Z", "team", "class"],
        other=["attacker_X", "attacker_Y", "attacker_Z", "weapon"]
    )
    
    highlights = []
    
    for _, kill in kills.iterrows():
        # Detecta airshot: vítima estava acima de Z normal
        if kill["Z"] > 150 and kill["weapon"] in ["tf_projectile_rocket", "tf_projectile_pipe"]:
            highlights.append({
                "type": "airshot",
                "tick": kill["tick"],
                "timestamp": kill["tick"] / 66,  # 66 ticks/s
                "attacker": kill["attacker_name"],
                "victim": kill["user_name"],
                "confidence": 0.9
            })
        
        # Medic pick: vítima é medic
        if kill["user_class"] == "medic":
            highlights.append({
                "type": "medic_pick",
                "tick": kill["tick"],
                "timestamp": kill["tick"] / 66,
                "attacker": kill["attacker_name"],
                "confidence": 0.7
            })
    
    return sorted(highlights, key=lambda x: x["confidence"], reverse=True)


# O worker HLAE (roda em Windows separado, chamado via API interna)
# backend/workers/hlae_worker.py

import subprocess
import json

def render_highlight(demo_path: str, tick: int, output_path: str):
    """
    Chama HLAE via CLI para renderizar o clip centrado no tick do highlight.
    Requer: HLAE instalado, TF2 instalado, SteamCMD autenticado.
    """
    
    hlae_cmd = [
        r"C:\HLAE\hlae.exe",
        "-game", r"C:\Steam\steamapps\common\Team Fortress 2\hl2.exe",
        "-guirecord",
        "-afxDetachRender",
        "-demo", demo_path,
        "-playdemo",
        f"+demo_gototick {tick - 66 * 3}",  # 3 segundos antes
        f"+mirv_deathmsg filter add attackerName * victimName * oc 1 oc_notex 1",
        f"+mirv_streams add normal",
        f"+mirv_streams record start",
        f"+host_timescale 0.5",  # slow-mo
    ]
    
    subprocess.run(hlae_cmd, check=True)
    
    # Depois, FFmpeg para montar o vídeo final
    subprocess.run([
        "ffmpeg", "-i", f"{output_path}/frame_%04d.png",
        "-c:v", "libx264", "-crf", "18", "-r", "60",
        f"{output_path}/highlight.mp4"
    ], check=True)