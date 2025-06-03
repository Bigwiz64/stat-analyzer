import os
import sys
import sqlite3
import time
from dotenv import load_dotenv
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path

# 🔐 Chargement variables d’environnement
load_dotenv()

# 📍 Connexion à la base
DB_PATH = get_db_path()
print(f"📁 Base de données utilisée : {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 📌 Ligue Australie
AUSTRALIA_LEAGUE_ID = 188

# 🎯 Paramètres CLI
SEASON = sys.argv[1] if len(sys.argv) > 1 else "2024"
FROM_DATE = sys.argv[2] if len(sys.argv) > 2 else "2024-10-01"
TO_DATE = sys.argv[3] if len(sys.argv) > 3 else "2025-05-01"

def insert_fixture(data):
    fixture = data["fixture"]
    league = data["league"]
    teams = data["teams"]
    goals = data["goals"]

    # ✅ Insertion match
    cursor.execute("""
        INSERT OR REPLACE INTO fixtures (id, date, league_id, home_team_id, away_team_id, home_goals, away_goals)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        fixture["id"], fixture["date"], league["id"],
        teams["home"]["id"], teams["away"]["id"],
        goals["home"], goals["away"]
    ))

    # ✅ Insertion équipes
    for side in ["home", "away"]:
        team = teams[side]
        cursor.execute("""
            INSERT OR IGNORE INTO teams (id, name, logo)
            VALUES (?, ?, ?)
        """, (team["id"], team["name"], team["logo"]))

    # ✅ Statistiques des joueurs
    try:
        stats_data = get_api_json("fixtures/players", params={"fixture": fixture["id"]}).get("response", [])
        for team_data in stats_data:
            team_id = team_data["team"]["id"]
            for entry in team_data["players"]:
                player = entry["player"]
                stats = entry["statistics"][0] if entry["statistics"] else {}

                player_id = player["id"]
                player_name = player["name"]
                position = player.get("position", "")
                minutes = stats.get("games", {}).get("minutes", 0)
                goals = stats.get("goals", {}).get("total", 0)
                assists = stats.get("goals", {}).get("assists", 0)

                cursor.execute("""
                    INSERT OR IGNORE INTO players (id, name, position)
                    VALUES (?, ?, ?)
                """, (player_id, player_name, position))

                cursor.execute("""
                    INSERT OR REPLACE INTO player_stats (player_id, fixture_id, team_id, minutes, goals, assists)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (player_id, fixture["id"], team_id, minutes, goals, assists))
    except Exception as e:
        print(f"❌ Erreur stats joueur match {fixture['id']} : {e}")

def fetch_australia_fixtures():
    print(f"📦 Récupération A-League 🇦🇺 - Saison {SEASON}")
    res = get_api_json("fixtures", params={
        "league": AUSTRALIA_LEAGUE_ID,
        "season": SEASON,
        "from": FROM_DATE,
        "to": TO_DATE
    })

    fixtures = res.get("response", [])
    print(f"📊 {len(fixtures)} match(s) trouvé(s).")

    for fixture in fixtures:
        insert_fixture(fixture)
        print(f"✅ Match {fixture['fixture']['id']} inséré.")
        time.sleep(0.5)

# 🚀 Lancement
if __name__ == "__main__":
    fetch_australia_fixtures()
    conn.commit()
    conn.close()
    print("🎉 Import terminé.")
