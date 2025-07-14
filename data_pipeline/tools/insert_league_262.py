import sqlite3
from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()

league_data = {
    "id": 262,
    "name": "Liga MX",
    "country": "Mexico",
    "logo": "https://media.api-sports.io/football/leagues/262.png",
    "flag": "https://media.api-sports.io/flags/mx.svg"
}

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO leagues (id, name, country, logo, flag)
        VALUES (?, ?, ?, ?, ?)
    """, (league_data["id"], league_data["name"], league_data["country"],
          league_data["logo"], league_data["flag"]))
    conn.commit()
    print(f"✅ Ligue {league_data['id']} ({league_data['name']}) insérée dans la base.")
