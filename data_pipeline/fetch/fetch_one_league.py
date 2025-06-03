import sys
import os
import sqlite3
import time
from dotenv import load_dotenv

# 🔁 Imports internes
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path

# 🔐 Chargement des variables d’environnement
load_dotenv()
DB_PATH = get_db_path()
print(f"\U0001F4C1 Base de données utilisée : {DB_PATH}")

# ✅ Paramètres depuis la ligne de commande
if len(sys.argv) < 4:
    print("❌ Utilisation : python fetch_one_league.py <league_id> <season> <from_date> <to_date>")
    sys.exit(1)

LEAGUE_ID = int(sys.argv[1])
SEASON = int(sys.argv[2])
FROM_DATE = sys.argv[3]
TO_DATE = sys.argv[4]

# ⚙️ Connexion
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# =========================
# 🔄 Insertion d'un match + stats
# =========================
def insert_fixture(data):
    fixture = data["fixture"]
    league = data["league"]
    teams = data["teams"]
    goals = data["goals"]

    # Skip si le match a déjà un score
    cursor.execute("SELECT home_goals, away_goals FROM fixtures WHERE id = ?", (fixture["id"],))
    result = cursor.fetchone()
    if result and result[0] is not None and result[1] is not None:
        return

    cursor.execute("""
        INSERT OR REPLACE INTO fixtures (id, date, league_id, home_team_id, away_team_id, home_goals, away_goals)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        fixture["id"], fixture["date"], league["id"],
        teams["home"]["id"], teams["away"]["id"],
        goals["home"], goals["away"]
    ))

    for side in ["home", "away"]:
        team = teams[side]
        cursor.execute("""
            INSERT OR IGNORE INTO teams (id, name, logo)
            VALUES (?, ?, ?)
        """, (team["id"], team["name"], team["logo"]))

    # Statistiques des joueurs
    try:
        stats_data = get_api_json("fixtures/players", params={"fixture": fixture["id"]}).get("response", [])
        for team_data in stats_data:
            team_id = team_data["team"]["id"]
            for entry in team_data["players"]:
                player = entry["player"]
                stats = entry["statistics"][0] if entry["statistics"] else {}

                cursor.execute("""
                    INSERT OR IGNORE INTO players (id, name, position)
                    VALUES (?, ?, ?)
                """, (player["id"], player["name"], player.get("position", "")))

                cursor.execute("""
                    INSERT OR REPLACE INTO player_stats (player_id, fixture_id, team_id, minutes, goals, assists)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    player["id"], fixture["id"], team_id,
                    stats.get("games", {}).get("minutes", 0),
                    stats.get("goals", {}).get("total", 0),
                    stats.get("goals", {}).get("assists", 0)
                ))

    except Exception as e:
        print(f"\u274c Erreur pour le match {fixture['id']} : {e}")

# =========================
# 📆 Récupération des matchs
# =========================
def fetch_fixtures():
    print(f"\U0001f4e6 Ligue {LEAGUE_ID} - Saison {SEASON} du {FROM_DATE} au {TO_DATE}")

    res = get_api_json("fixtures", params={
        "league": LEAGUE_ID,
        "season": SEASON,
        "from": FROM_DATE,
        "to": TO_DATE
    })
    fixtures = res.get("response", [])
    print(f"  ✅ {len(fixtures)} match(s) reçu(s)")

    for fixture in fixtures:
        insert_fixture(fixture)
        time.sleep(0.3)

# =========================
# 🚀 Lancement
# =========================
if __name__ == "__main__":
    fetch_fixtures()
    conn.commit()
    conn.close()
    print("\n\U0001f389 Terminé avec succès.")
