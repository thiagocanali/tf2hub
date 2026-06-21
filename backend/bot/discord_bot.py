# backend/bot/discord_bot.py
import discord
from discord.ext import commands, tasks

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@tasks.loop(hours=168)  # toda semana
async def post_weekly_highlights():
    channel = bot.get_channel(SEU_CANAL_ID)
    
    # Busca destaques da semana na API do TF2Hub
    highlights = await fetch_weekly_highlights()
    
    embed = discord.Embed(
        title="🏆 Destaques da Semana — TF2Hub BR",
        color=0xE8593C
    )
    
    for h in highlights[:5]:
        embed.add_field(
            name=f"**{h['player_name']}** como {h['class']}",
            value=f"[🔗 Ver log]({h['log_url']}) · {h['metric_label']}: **{h['value']}**",
            inline=False
        )
    
    await channel.send(embed=embed)

# Vinculação Discord ↔ perfil (OAuth2 no frontend Next.js)
# O flow é: Discord OAuth → callback → salva discord_id na tabela players