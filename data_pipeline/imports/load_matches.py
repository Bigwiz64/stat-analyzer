import sqlite3
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from data_pipeline.api_utils.path_utils import get_db_path

load_dotenv()

API_KEY = os.getenv("API_SPORT_KEY")
HEADERS = {"x-apisports-key": API_KEY}

DB_PATH = get_db_path()

def get_league_ids():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM leagues")
        return [row[0] for row in cursor.fetchall()]

def get_yesterday():
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

def fetch_fixtures(league_id, date):
    url = "https://v3.football.api-sports.io/fixtures"
    params = {
        "league": league_id,
        "date": date,
        "season": 2024  # ← à adapter si tu changes de saison
    }
    res = requests.get(url, headers=HEADERS, params=params)

    print(f"\n📡 Appel API fixtures : {res.url}")
    print(f"➡️ Status : {res.status_code}")
    try:
        data = res.json()
        print(f"↩️ Résultat brut : {data}")
    except Exception as e:
        print(f"❌ Erreur lors du parsing JSON : {e}")
        return []

    return data.get("response", [])

def fetch_players_stats(fixture_id):
    url = "https://v3.football.api-sports.io/fixtures/players"
    params = {"fixture": fixture_id}
    res = requests.get(url, headers=HEADERS, params=params)
    return res.json().get("response", [])

def insert_data(fixture, stats):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Teams
        for team in [fixture['teams']['home'], fixture['teams']['away']]:
            cursor.execute("INSERT OR IGNORE INTO teams (id, name, country) VALUES (?, ?, ?)",
                (team['id'], team['name'], team.get('country', '')))

        # Fixture
        cursor.execute("""
            INSERT OR IGNORE INTO fixtures (id, date, league_id, home_team_id, away_team_id, home_goals, away_goals)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            fixture['fixture']['id'],
            fixture['fixture']['date'],
            fixture['league']['id'],
            fixture['teams']['home']['id'],
            fixture['teams']['away']['id'],
            fixture['goals']['home'],
            fixture['goals']['away']
        ))

        # Players & Stats
        for team in stats:
            team_id = team['team']['id']
            for player_data in team['players']:
                player = player_data['player']
                stat = player_data['statistics'][0]

                cursor.execute("INSERT OR IGNORE INTO players (id, name, position) VALUES (?, ?, ?)",
                    (player['id'], player['name'], stat['games'].get('position', '')))

                cursor.execute("""
                    INSERT INTO player_stats (fixture_id, player_id, team_id, goals, assists, yellow_cards, red_cards, minutes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fixture['fixture']['id'],
                    player['id'],
                    team_id,
                    stat['goals'].get('total', 0),
                    stat['goals'].get('assists', 0),
                    stat['cards'].get('yellow', 0),
                    stat['cards'].get('red', 0),
                    stat['games'].get('minutes', 0)
                ))

        conn.commit()

def main():
    leagues = get_league_ids()
    date = get_yesterday()
    print(f"📅 Chargement des matchs du {date}...")

    for league_id in leagues:
        fixtures = fetch_fixtures(league_id, date)
        print(f"➡️ Ligue {league_id} : {len(fixtures)} match(s) trouvé(s)")

        for fixture in fixtures:
            fixture_id = fixture['fixture']['id']
            stats = fetch_players_stats(fixture_id)

            if stats:
                insert_data(fixture, stats)
                print(f"✅ Match {fixture_id} inséré avec stats.")
            else:
                print(f"⚠️ Pas de stats pour le match {fixture_id}")

if __name__ == "__main__":
    main()
