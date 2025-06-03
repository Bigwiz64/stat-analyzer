import requests
import sqlite3
import os
from data_pipeline.api_utils.path_utils import get_db_path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("API_SPORT_KEY")
HEADERS = {"x-apisports-key": API_KEY}
DB_PATH = get_db_path()


# Liste de ligues (15 ligues)
LEAGUES = [61, 62, 39, 140, 78, 135, 88, 94, 203, 141, 179, 4, 40, 79]

# Saison à cibler
SEASON = 2024

def fetch_all_fixtures(league_id, season):
    fixtures = []
    page = 1

    while True:
        print(f"📦 Récupération Ligue {league_id} - Page {page}")
        res = requests.get(
            "https://v3.football.api-sports.io/fixtures",
            headers=HEADERS,
            params={
                "league": league_id,
                "season": season,
                "page": page
            }
        )

        data = res.json()

        if "response" not in data or not data["response"]:
            break

        fixtures += data["response"]

        # Pagination
        if page >= data.get("paging", {}).get("total", 1):
            break
        page += 1

    return fixtures


def insert_fixtures(fixtures):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for fixture in fixtures:
            f = fixture["fixture"]
            l = fixture["league"]
            t = fixture["teams"]
            g = fixture["goals"]

            fixture_id = f["id"]
            date = f["date"]
            league_id = l["id"]
            home_team_id = t["home"]["id"]
            away_team_id = t["away"]["id"]
            home_goals = g["home"]
            away_goals = g["away"]

            cursor.execute("""
                INSERT OR IGNORE INTO fixtures 
                (id, date, league_id, home_team_id, away_team_id, home_goals, away_goals)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                fixture_id, date, league_id,
                home_team_id, away_team_id,
                home_goals, away_goals
            ))

        conn.commit()


if __name__ == "__main__":
    total = 0
    for league_id in LEAGUES:
        fixtures = fetch_all_fixtures(league_id, SEASON)
        insert_fixtures(fixtures)
        print(f"✅ {len(fixtures)} matchs ajoutés pour la ligue {league_id}")
        total += len(fixtures)
    print(f"\n🎯 Total des matchs récupérés : {total}")
