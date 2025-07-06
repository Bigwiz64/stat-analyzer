import sqlite3
from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()

league = {
    "id": 242,
    "name": "Serie A",
    "country": "Ecuador",
    "logo": "https://media.api-sports.io/football/leagues/242.png",
    "flag": "https://media.api-sports.io/flags/ec.svg"
}

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO leagues (id, name, country, logo, flag)
        VALUES (?, ?, ?, ?, ?)
    """, (league["id"], league["name"], league["country"], league["logo"], league["flag"]))
    conn.commit()

print("✅ Ligue 242 (Serie A Équateur) insérée dans la base.")
