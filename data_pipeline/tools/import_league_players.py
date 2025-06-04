import os
import requests
import sqlite3
import sys

from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from data_pipeline.api_utils.path_utils import get_db_path


load_dotenv()

# 📍 Connexion à la base
DB_PATH = get_db_path()
print(f"\U0001F4C1 Base de données utilisée : {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

API_KEY = os.getenv("API_SPORT_KEY")
API_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

def get_team_ids_from_league(league_id):
    cursor.execute("SELECT id FROM teams WHERE league_id = ?", (league_id,))
    return [row[0] for row in cursor.fetchall()]

def insert_player(player):
    cursor.execute("""
        INSERT OR IGNORE INTO players (id, name, position, age, country_flag)
        VALUES (?, ?, ?, ?, ?)
    """, (
        player["id"],
        player["name"],
        player["position"],
        player["age"],
        player["nationality"]
    ))
    conn.commit()

def fetch_and_store_players(team_id):
    print(f"📡 Requête API pour team_id {team_id}...")

    url = f"https://v3.football.api-sports.io/players/squads?team={team_id}"
    headers = {"x-apisports-key": API_KEY}

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Erreur API pour team_id {team_id} : {response.status_code}")
        return

    data = response.json()
    
    # Correction ici : on traite data["response"] comme une liste
    if not data.get("response"):
        print(f"⚠️ Aucune donnée de joueur pour l'équipe {team_id}")
        return

    # Cas attendu : liste contenant un dict avec la clé 'players'
    try:
        squad = data["response"][0]  # On récupère le premier élément
        players = squad["players"]
    except (IndexError, KeyError) as e:
        print(f"❌ Structure inattendue pour l'équipe {team_id} : {e}")
        return

    for player in players:
        player_id = player["id"]
        name = player["name"]
        position = player.get("position", "")
        age = player.get("age")
        flag = player.get("nationality")

        cursor.execute("""
            INSERT OR IGNORE INTO players (id, name, position, age, country_flag)
            VALUES (?, ?, ?, ?, ?)
        """, (player_id, name, position, age, flag))
        conn.commit()

    print(f"✅ {len(players)} joueurs importés pour l'équipe {team_id}")


def main(league_id):
    print(f"📥 Import des joueurs de la ligue ID : {league_id}")
    team_ids = get_team_ids_from_league(league_id)
    print(f"➡️ {len(team_ids)} équipes trouvées : {team_ids}")
    for team_id in team_ids:
        fetch_and_store_players(team_id)

if __name__ == "__main__":
    # 🇫🇮 Ligue Finlandaise : 244 (ou autre ID de ton choix)
    main(244)
