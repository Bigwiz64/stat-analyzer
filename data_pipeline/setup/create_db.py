import sqlite3
from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()

conn = sqlite3.connect("data.db")
cursor = conn.cursor()

# Ligues suivies
cursor.execute("""
CREATE TABLE IF NOT EXISTS leagues (
    id INTEGER PRIMARY KEY,
    name TEXT
)
""")

# Équipes
cursor.execute("""
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY,
    name TEXT,
    country TEXT
)
""")

# Matchs
cursor.execute("""
CREATE TABLE IF NOT EXISTS fixtures (
    id INTEGER PRIMARY KEY,
    date TEXT,
    league_id INTEGER,
    home_team_id INTEGER,
    away_team_id INTEGER,
    home_goals INTEGER,
    away_goals INTEGER
)
""")

# Joueurs
cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    name TEXT,
    position TEXT
)
""")

# Statistiques d’un joueur pour un match
cursor.execute("""
CREATE TABLE IF NOT EXISTS player_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fixture_id INTEGER,
    player_id INTEGER,
    team_id INTEGER,
    goals INTEGER,
    assists INTEGER,
    yellow_cards INTEGER,
    red_cards INTEGER,
    minutes INTEGER
)
""")

conn.commit()
conn.close()
