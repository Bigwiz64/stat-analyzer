import sqlite3
import os
from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()


schema = """
-- -- Table des équipes
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    logo TEXT
);

-- Table des ligues
CREATE TABLE IF NOT EXISTS leagues (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT,
    logo TEXT,
    flag TEXT
);

-- Table des matchs
CREATE TABLE IF NOT EXISTS fixtures (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    league_id INTEGER,
    home_team_id INTEGER,
    away_team_id INTEGER,
    home_goals INTEGER,
    away_goals INTEGER,
    FOREIGN KEY (league_id) REFERENCES leagues(id),
    FOREIGN KEY (home_team_id) REFERENCES teams(id),
    FOREIGN KEY (away_team_id) REFERENCES teams(id)
);

-- Table des joueurs
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    position TEXT
);

-- Table des statistiques des joueurs par match
CREATE TABLE IF NOT EXISTS player_stats (
    player_id INTEGER,
    fixture_id INTEGER,
    team_id INTEGER,
    minutes INTEGER,
    goals INTEGER,
    assists INTEGER,
    PRIMARY KEY (player_id, fixture_id),
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (fixture_id) REFERENCES fixtures(id),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

"""


with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.executescript(schema)
    conn.commit()

print("✅ Base de données initialisée avec succès.")
