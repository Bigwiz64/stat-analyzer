import os
import sqlite3
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from data_pipeline.api_utils.utils_api import call_api
from data_pipeline.api_utils.path_utils import get_db_path

# 🔐 Chargement .env
load_dotenv()
DB_PATH = get_db_path()

# 📌 Ligues suivies
LEAGUE_IDS = [
    61, 62, 39, 140, 78, 135, 88,
    94, 203, 141, 179, 4, 40, 79
]

def daterange(start, end):
    for n in range((end - start).days + 1):
        yield start + timedelta(n)

def fetch_fixtures(league_id, date_obj, season):
    return call_api("fixtures", {
        "league": league_id,
        "season": season,
        "date": date_obj.strftime("%Y-%m-%d")
    }).get("response", [])

def fetch_players_stats(fixture_id):
    return call_api("fixtures/players", {
        "fixture": fixture_id
    }).get("response", [])

def insert_data(fixture, stats):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 🏟 Équipes
        for team in [fixture["teams"]["home"], fixture["teams"]["away"]]:
            cursor.execute("""
                INSERT OR IGNORE INTO teams (id, name, country)
                VALUES (?, ?, ?)
            """, (team["id"], team["name"], team.get("country", "")))

        # 📆 Match
        cursor.execute("""
            INSERT OR IGNORE INTO fixtures (
                id, date, league_id, home_team_id, away_team_id, home_goals, away_goals
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            fixture["fixture"]["id"],
            fixture["fixture"]["date"],
            fixture["league"]["id"],
            fixture["teams"]["home"]["id"],
            fixture["teams"]["away"]["id"],
            fixture["goals"]["home"],
            fixture["goals"]["away"]
        ))

        # 👤 Joueurs
        for team in stats:
            team_id = team["team"]["id"]
            for player_data in team["players"]:
                player = player_data["player"]
                stat = player_data["statistics"][0] if player_data["statistics"] else {}

                cursor.execute("""
                    INSERT OR IGNORE INTO players (id, name, position)
                    VALUES (?, ?, ?)
                """, (player["id"], player["name"], stat.get("games", {}).get("position", "")))

                cursor.execute("""
                    INSERT INTO player_stats (
                        fixture_id, player_id, team_id, goals, assists, yellow_cards, red_cards, minutes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fixture["fixture"]["id"],
                    player["id"],
                    team_id,
                    stat.get("goals", {}).get("total", 0),
                    stat.get("goals", {}).get("assists", 0),
                    stat.get("cards", {}).get("yellow", 0),
                    stat.get("cards", {}).get("red", 0),
                    stat.get("games", {}).get("minutes", 0)
                ))

        conn.commit()

def main():
    if len(sys.argv) != 4:
        print("❌ Utilisation attendue : python load_season_2024.py <saison> <date_debut> <date_fin>")
        print("Exemple : python load_season_2024.py 2024 2025-04-01 2025-06-30")
        return

    season = int(sys.argv[1])
    start_date = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()
    end_date = datetime.strptime(sys.argv[3], "%Y-%m-%d").date()

    for day in daterange(start_date, end_date):
        print(f"\n📅 {day.strftime('%Y-%m-%d')}")
        for league_id in LEAGUE_IDS:
            fixtures = fetch_fixtures(league_id, day, season)
            print(f"  ➡️ Ligue {league_id} : {len(fixtures)} match(s) trouvé(s)")

            for fixture in fixtures:
                fixture_id = fixture["fixture"]["id"]
                stats = fetch_players_stats(fixture_id)

                if stats:
                    insert_data(fixture, stats)
                    print(f"  ✅ Match {fixture_id} inséré avec stats.")
                else:
                    print(f"  ⚠️ Pas de stats pour le match {fixture_id}")

if __name__ == "__main__":
    main()
