import requests
import sqlite3

DB_PATH = "/Users/morane/stat-analyzer/data_pipeline/db/data.db"
API_KEY = "5343ef8cf97a1d2a8e6d50fd7409cb4e"
TEAM_ID = 327  # L’équipe de Kasper Høgh
SEASON = 2025

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "v3.football.api-sports.io"
}

def test_update_single_team(team_id, season):
    print(f"📡 Test mise à jour pour l'équipe {team_id}, saison {season}")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        params = {
            "team": team_id,
            "season": season
        }

        try:
            response = requests.get("https://v3.football.api-sports.io/players", headers=headers, params=params)
            data = response.json()

            if data.get("errors"):
                print(f"❌ Erreur API : {data['errors']}")
                return

            for player in data["response"]:
                p = player["player"]
                stats_list = player.get("statistics", [])

                if not stats_list:
                    print(f"⚠️ Aucune stat pour {p.get('name')} — ignoré")
                    continue

                stats = stats_list[0]

                player_id = p.get("id")
                name = p.get("name")
                firstname = p.get("firstname")
                lastname = p.get("lastname")
                age = p.get("age")
                position = stats.get("games", {}).get("position")
                nationality = p.get("nationality")
                country_flag = nationality
                team_id_stat = stats.get("team", {}).get("id", team_id)
                photo = p.get("photo")
                birth_date = p.get("birth", {}).get("date")
                birth_place = p.get("birth", {}).get("place")
                birth_country = p.get("birth", {}).get("country")
                height = p.get("height")
                weight = p.get("weight")
                rating = stats.get("games", {}).get("rating")
                injured = p.get("injured")

                cursor.execute("""
                    INSERT OR REPLACE INTO players (
                        id, name, firstname, lastname, position, age,
                        country, country_flag, team_id, photo,
                        birth_date, birth_place, birth_country,
                        height, weight, rating, injured
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    player_id, name, firstname, lastname, position, age,
                    nationality, country_flag, team_id_stat, photo,
                    birth_date, birth_place, birth_country,
                    height, weight, rating, injured
                ))

                print(f"✅ Joueur mis à jour : {player_id} - {name}")

        except Exception as e:
            print(f"❌ Exception : {e}")

test_update_single_team(TEAM_ID, SEASON)
