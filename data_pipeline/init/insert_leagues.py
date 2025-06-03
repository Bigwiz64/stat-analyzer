import sqlite3
import os
import requests
from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()
API_KEY = os.getenv("API_FOOTBALL_KEY")
API_URL = "https://v3.football.api-sports.io/leagues"

HEADERS = {
    "x-apisports-key": API_KEY
}

LEAGUE_IDS = [61, 62, 39, 140, 78, 135, 88, 94, 203, 141, 179, 4, 40, 79]

def update_league_logos():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for league_id in LEAGUE_IDS:
            response = requests.get(API_URL, headers=HEADERS, params={"id": league_id})
            data = response.json()

            if data.get("response"):
                league = data["response"][0]["league"]
                country = data["response"][0]["country"]

                logo = league.get("logo")
                flag = country.get("flag")
                name = league.get("name")
                country_name = country.get("name")

                cursor.execute("""
                    INSERT OR REPLACE INTO leagues (id, name, country, logo, flag)
                    VALUES (?, ?, ?, ?, ?)
                """, (league_id, name, country_name, logo, flag))

                print(f"✅ {name} ({country_name}) mis à jour")
            else:
                print(f"❌ Aucune donnée trouvée pour league_id={league_id}")
        conn.commit()

if __name__ == "__main__":
    update_league_logos()
