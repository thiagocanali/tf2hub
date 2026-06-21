# backend/alembic/versions/001_expand_schema.py

# Tabela de jogadores com ELO por formato
CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    steam_id VARCHAR(64) UNIQUE NOT NULL,
    discord_id VARCHAR(64),
    display_name VARCHAR(128),
    created_at TIMESTAMP DEFAULT NOW()
);

# ELO separado por formato (6v6, HL, 4v4, Mix)
CREATE TABLE player_ratings (
    id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(id),
    format VARCHAR(16) NOT NULL,  -- '6v6', 'highlander', '4v4', 'mix'
    elo INT DEFAULT 1000,
    peak_elo INT DEFAULT 1000,
    games_played INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(player_id, format)
);

# Cada log já tem um formato
ALTER TABLE logs ADD COLUMN format VARCHAR(16) DEFAULT '6v6';
ALTER TABLE logs ADD COLUMN performance_score FLOAT;  -- calculado na ingestão

# Médias históricas por jogador+classe+formato (atualizada após cada log)
CREATE TABLE player_class_averages (
    id SERIAL PRIMARY KEY,
    player_id INT REFERENCES players(id),
    class_name VARCHAR(32),  -- 'soldier', 'medic', etc.
    format VARCHAR(16),
    avg_dpm FLOAT DEFAULT 0,
    avg_kda FLOAT DEFAULT 0,
    avg_heals_per_min FLOAT DEFAULT 0,  -- Medic
    avg_airshots FLOAT DEFAULT 0,        -- Soldier/Demo
    sample_size INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(player_id, class_name, format)
);