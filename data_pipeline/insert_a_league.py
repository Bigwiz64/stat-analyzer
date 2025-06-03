import sys
import os
import sqlite3

# ➕ Ajout du chemin pour importer data_pipeline
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api_utils.path_utils import get_db_path

DB_PATH = get_db_path()
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Données pour la A-League
league_id = 188
name = "A-League"
country = "Australia"
logo = "https://media-4.api-sports.io/football/leagues/188.png"
flag = "https://media-4.api-sports.io/flags/au.svg"

# Insertion
cursor.execute("""
    INSERT OR IGNORE INTO leagues (id, name, country, logo, flag)
    VALUES (?, ?, ?, ?, ?)
""", (league_id, name, country, logo, flag))

conn.commit()
conn.close()

print(f"✅ A-League insérée dans la base ({DB_PATH})")
