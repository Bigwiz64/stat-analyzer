import requests
import sqlite3
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

API_KEY = os.getenv("API_SPORT_KEY")
LEAGUE_ID = 242  # Serie A Équateur
SEASON = 2025

DB_PATH = "/Users/morane/stat-analyzer/data_pipeline/db/data.db"  # À adapter si besoin

HEADERS = {
    "x-apisports-key": API_KEY
}

def fetch_and_insert_teams_for_league(league_id, season):
    url = f"https://v3.football.api-sports.io/teams?league={league_id}&season={season}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    if "response" not in data:
        print("❌ Erreur : réponse invalide de l'API")
        print(data)
        return

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        for team_info in data["response"]:
            team = team_info["team"]
            team_id = team["id"]
            name = team["name"]
            logo = team["logo"]

            cursor.execute("SELECT id FROM teams WHERE id = ?", (team_id,))
            exists = cursor.fetchone()

            if not exists:
                cursor.execute(
                    "INSERT INTO teams (id, name, logo) VALUES (?, ?, ?)",
                    (team_id, name, logo)
                )
                print(f"✅ Équipe ajoutée : {name} (ID {team_id})")
            else:
                print(f"⏭️ Équipe déjà présente : {name} (ID {team_id})")

        conn.commit()

if __name__ == "__main__":
    if not API_KEY:
        print("❌ Clé API manquante. Vérifie ton fichier .env.")
    else:
        fetch_and_insert_teams_for_league(LEAGUE_ID, SEASON)
        print("✅ Import terminé.")
