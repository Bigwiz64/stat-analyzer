import sys
import sqlite3
import os
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from data_pipeline.api_utils.path_utils import get_db_path
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_SPORT_KEY")
HEADERS = {"x-apisports-key": API_KEY}

DB_PATH = get_db_path()


def update_logos():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM leagues")
        league_ids = [row[0] for row in cursor.fetchall()]

        for league_id in league_ids:
            print(f"🔄 Traitement de la ligue {league_id}...")
            res = requests.get(
                "https://v3.football.api-sports.io/leagues",
                headers=HEADERS,
                params={"id": league_id}
            )

            data = res.json()
            if data["response"]:
                league_info = data["response"][0]
                logo = league_info["league"]["logo"]
                flag = league_info["country"].get("flag", "")

                cursor.execute("""
                    UPDATE leagues
                    SET logo = ?, flag = ?
                    WHERE id = ?
                """, (logo, flag, league_id))

                print(f"✅ Ligue {league_id} mise à jour avec logo + drapeau.")
            else:
                print(f"⚠️ Aucune donnée pour la ligue {league_id}.")

        conn.commit()

if __name__ == "__main__":
    update_logos()
