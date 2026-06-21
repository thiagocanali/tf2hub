# backend/app/models.py
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, UniqueConstraint, Text
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    steam_id = Column(String(64), unique=True, nullable=False, index=True)
    discord_id = Column(String(64), nullable=True)
    display_name = Column(String(128), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    ratings = relationship("PlayerRating", back_populates="player")
    class_averages = relationship("PlayerClassAverage", back_populates="player")
    logs = relationship("LogEntry", back_populates="player")
    watchdog_flags = relationship("WatchdogFlag", back_populates="player")


class PlayerRating(Base):
    __tablename__ = "player_ratings"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    format = Column(String(16), nullable=False)  # '6v6', 'highlander', '4v4', 'mix'
    elo = Column(Integer, default=1000)
    peak_elo = Column(Integer, default=1000)
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    player = relationship("Player", back_populates="ratings")

    __table_args__ = (UniqueConstraint("player_id", "format"),)


class PlayerClassAverage(Base):
    __tablename__ = "player_class_averages"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    class_name = Column(String(32), nullable=False)  # 'soldier', 'medic', etc.
    format = Column(String(16), nullable=False)
    # Métricas gerais
    avg_dpm = Column(Float, default=0.0)
    avg_kda = Column(Float, default=0.0)
    # Métricas específicas por classe
    avg_heals_per_min = Column(Float, default=0.0)   # Medic
    avg_ubers_per_game = Column(Float, default=0.0)   # Medic
    avg_airshots = Column(Float, default=0.0)          # Soldier / Demo
    avg_headshots_pct = Column(Float, default=0.0)     # Sniper
    avg_backstabs = Column(Float, default=0.0)         # Spy
    avg_captures = Column(Float, default=0.0)          # Scout
    sample_size = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    player = relationship("Player", back_populates="class_averages")

    __table_args__ = (UniqueConstraint("player_id", "class_name", "format"),)


class LogEntry(Base):
    __tablename__ = "log_entries"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    logs_tf_id = Column(Integer, unique=True, nullable=False, index=True)  # ID do logs.tf
    format = Column(String(16), default="6v6")
    class_played = Column(String(32), nullable=True)
    # Stats da partida
    dpm = Column(Float, default=0.0)
    kills = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    kda = Column(Float, default=0.0)
    heals_received = Column(Integer, default=0)
    heals_given = Column(Integer, default=0)
    ubers = Column(Integer, default=0)
    drops = Column(Integer, default=0)
    airshots = Column(Integer, default=0)
    headshots = Column(Integer, default=0)
    headshots_pct = Column(Float, default=0.0)
    backstabs = Column(Integer, default=0)
    captures = Column(Integer, default=0)
    duration_seconds = Column(Integer, default=0)
    result = Column(String(8), nullable=True)  # 'win', 'loss', 'tie'
    # Score calculado
    performance_score = Column(Float, nullable=True)
    played_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    player = relationship("Player", back_populates="logs")


class WatchdogFlag(Base):
    __tablename__ = "watchdog_flags"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    metric = Column(String(64), nullable=False)
    class_name = Column(String(32), nullable=False)
    z_score = Column(Float, nullable=False)
    player_avg = Column(Float, nullable=False)
    tier_avg = Column(Float, nullable=False)
    severity = Column(String(16), nullable=False)  # 'medium', 'high'
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    player = relationship("Player", back_populates="watchdog_flags")