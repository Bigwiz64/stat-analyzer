import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from dotenv import load_dotenv
from data_pipeline.api_utils.utils_api import get_api_json as call_api 
from data_pipeline.api_utils.path_utils import get_db_path
import sqlite3


load_dotenv()
DB_PATH = get_db_path()

# 🏟️ Ligues à ajouter
LEAGUES = [
    61, 62, 39, 140, 78, 135, 88, 94, 203, 141,
    179, 4, 40, 79, 103, 169, 136, 253, 195  # + Norvège, Chine, etc.
]

def insert_league_info(league_id):
    data = call_api("leagues", {"id": league_id})
    if not data or not data.get("response"):
        print(f"❌ Impossible de récupérer les infos pour la ligue {league_id}")
        return

    league = data["response"][0]["league"]
    country = data["response"][0]["country"]

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO leagues (id, name, country, logo, flag)
            VALUES (?, ?, ?, ?, ?)
        """, (
            league["id"],
            league["name"],
            country["name"],
            league["logo"],
            country.get("flag", "")
        ))

        print(f"✅ Ligue ajoutée : {league['name']} ({country['name']})")

def main():
    print(f"📁 Base utilisée : {DB_PATH}")
    for league_id in LEAGUES:
        insert_league_info(league_id)

if __name__ == "__main__":
    main()
