import os
import sqlite3
from dotenv import load_dotenv
from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path
from data_pipeline.fetch.import_fixtures_2024 import update_players_table


load_dotenv()
API_KEY = os.getenv("API_SPORT_KEY")
DB_PATH = get_db_path()
SEASON = "2025"

def insert_team(team_id, name, logo, country, league_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO teams (id, name, logo, country, league_id)
        VALUES (?, ?, ?, ?, ?)
    """, (team_id, name, logo, country, league_id))
    conn.commit()
    conn.close()

def import_mls_teams_and_players():
    print("📦 Récupération des équipes MLS (ligue 253)...")
    res = get_api_json("teams", params={"league": 253, "season": SEASON})
    teams = res.get("response", [])
    
    team_ids = []
    for entry in teams:
        team = entry["team"]
        country = entry["venue"]["city"] or "USA"
        insert_team(team["id"], team["name"], team["logo"], country, 253)
        team_ids.append(team["id"])
        print(f"✅ Équipe ajoutée : {team['name']} ({team['id']})")

    print(f"\n🎯 Import des joueurs pour {len(team_ids)} équipes MLS...")
    update_players_table(team_ids, API_KEY, SEASON)

if __name__ == "__main__":
    import_mls_teams_and_players()
