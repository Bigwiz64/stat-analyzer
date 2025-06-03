# data_pipeline/update_team_logos.py

import sqlite3
import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_SPORT_KEY")
HEADERS = {"x-apisports-key": API_KEY}

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

def update_team_logos():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Récupère tous les IDs d'équipes utilisés dans les matchs
        cursor.execute("""
            SELECT DISTINCT id FROM teams
        """)
        team_ids = [row[0] for row in cursor.fetchall()]

        for team_id in team_ids:
            print(f"🔄 Traitement équipe {team_id}...")
            res = requests.get(
                "https://v3.football.api-sports.io/teams",
                headers=HEADERS,
                params={"id": team_id}
            )
            data = res.json()
            if data["response"]:
                logo = data["response"][0]["team"]["logo"]
                cursor.execute("UPDATE teams SET logo = ? WHERE id = ?", (logo, team_id))
                print(f"✅ Logo mis à jour pour équipe {team_id}")
            else:
                print(f"⚠️ Aucune donnée pour l’équipe {team_id}")

        conn.commit()
        print("✅ Mise à jour terminée.")

if __name__ == "__main__":
    update_team_logos()
