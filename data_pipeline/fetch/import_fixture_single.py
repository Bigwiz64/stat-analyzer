import sys
import os
import sqlite3
import time
from dotenv import load_dotenv

# 🔁 Import chemins et API
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path

# 🔐 Chargement .env
load_dotenv()

# 📍 Connexion à la base
DB_PATH = get_db_path()
print(f"📁 Base de données utilisée : {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def format_season(year):
    return f"{year}-{year + 1}"

LEAGUES = [78]  # Bundesliga

SEASON_BY_LEAGUE = {
    103: 2025,
    104: 2025,
    169: 2025,
    136: 2024,
    253: 2025,
    188: 2025
}

DEFAULT_SEASON = 2024
FROM_DATE = sys.argv[1] if len(sys.argv) > 1 else "2024-08-01"
TO_DATE = sys.argv[2] if len(sys.argv) > 2 else "2025-07-30"
MODE = sys.argv[3] if len(sys.argv) > 3 else "complet"

FIXTURE_ID = None
if "--fixture" in sys.argv:
    try:
        FIXTURE_ID = int(sys.argv[sys.argv.index("--fixture") + 1])
    except:
        print("❌ Mauvais usage de --fixture : il faut fournir un ID.")
        sys.exit(1)

def insert_player_stats(fixture_id, season_str):
    cursor.execute("SELECT COUNT(*) FROM player_stats WHERE fixture_id = ?", (fixture_id,))
    count = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(minutes), SUM(goals), SUM(assists) FROM player_stats WHERE fixture_id = ?", (fixture_id,))
    minutes_sum, goals_sum, assists_sum = cursor.fetchone()

    if count > 0 and (minutes_sum or 0) == 0 and (goals_sum or 0) == 0 and (assists_sum or 0) == 0:
        print(f"🔁 Réimport des stats joueurs pour match {fixture_id} (stats nulles)")
        cursor.execute("DELETE FROM player_stats WHERE fixture_id = ?", (fixture_id,))
    elif count > 0:
        print(f"🔁 Réimport forcé pour vérif xG match {fixture_id}")
        cursor.execute("DELETE FROM player_stats WHERE fixture_id = ?", (fixture_id,))

    try:
        stats_data = get_api_json("fixtures/players", params={"fixture": fixture_id}).get("response", [])

        for team_data in stats_data:
            team_id = team_data["team"]["id"]
            for entry in team_data["players"]:
                player = entry["player"]
                stats = entry["statistics"][0] if entry["statistics"] else {}

                print(f"👤 {player['name']} — Stats complètes : {stats}")

                cursor.execute("""
                    INSERT OR IGNORE INTO players (id, name, position)
                    VALUES (?, ?, ?)
                """, (
                    player["id"],
                    player["name"],
                    player.get("position", "")
                ))

                cursor.execute("""
                    INSERT OR REPLACE INTO player_stats (
                        player_id, fixture_id, team_id, minutes, goals, assists,
                        shots_total, shots_on_target,
                        xg, xa,
                        penalty_scored, penalty_missed,
                        yellow_cards, red_cards,
                        season
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    player["id"], fixture_id, team_id,
                    stats.get("games", {}).get("minutes", 0),
                    stats.get("goals", {}).get("total", 0),
                    stats.get("goals", {}).get("assists", 0),
                    stats.get("shots", {}).get("total", 0),
                    stats.get("shots", {}).get("on", 0),
                    stats.get("expected", {}).get("goals", 0),
                    stats.get("expected", {}).get("assists", 0),
                    stats.get("penalty", {}).get("scored", 0),
                    stats.get("penalty", {}).get("missed", 0),
                    stats.get("cards", {}).get("yellow", 0),
                    stats.get("cards", {}).get("red", 0),
                    str(season_str)
                ))

        print(f"✅ Stats joueurs insérées pour match {fixture_id}")

    except Exception as e:
        print(f"❌ Erreur stats joueurs match {fixture_id} : {e}")

def insert_fixture_events(fixture_id):
    print(f"🔁 Réinsertion forcée des événements du match {fixture_id}")
    cursor.execute("DELETE FROM fixture_events WHERE fixture_id = ?", (fixture_id,))

    try:
        events_data = get_api_json("fixtures/events", params={"fixture": fixture_id}).get("response", [])
        print(f"📆 {len(events_data)} événements récupérés pour {fixture_id}")

        for event in events_data:
            elapsed = event.get("time", {}).get("elapsed")
            extra = event.get("time", {}).get("extra") or 0
            minute = (elapsed + extra) if elapsed is not None else None

            team_id = event["team"]["id"]
            player = event.get("player")
            assist = event.get("assist")
            player_id = player["id"] if player else None
            assist_id = assist["id"] if assist else None

            print(f" - {event['type']} | {event['detail']} | minute: {minute}")

            cursor.execute("""
                INSERT INTO fixture_events (
                    fixture_id, team_id, player_id, assist_id, type, detail, comments, elapsed, extra, minute
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fixture_id,
                team_id,
                player_id,
                assist_id,
                event["type"],
                event["detail"],
                event.get("comments"),
                elapsed,
                extra,
                minute
            ))

        conn.commit()
        print("✅ Événements insérés avec succès.")

    except Exception as e:
        print(f"❌ Erreur événements match {fixture_id} : {e}")

def fetch_fixtures(league_id):
    season_api = SEASON_BY_LEAGUE.get(league_id, DEFAULT_SEASON)
    season_str = format_season(season_api)
    print(f"📦 Ligue {league_id} | Saison API: {season_api} | Saison Base: {season_str} | {FROM_DATE} → {TO_DATE}")

    res = get_api_json("fixtures", params={
        "league": league_id,
        "season": season_api,
        "from": FROM_DATE,
        "to": TO_DATE
    })

    fixtures = res.get("response", [])
    total_added = 0

    for fixture in fixtures:
        insert_player_stats(fixture["fixture"]["id"], season_str)
        insert_fixture_events(fixture["fixture"]["id"])
        total_added += 1

    print(f"✅ {total_added} matchs traités pour la ligue {league_id}")
    time.sleep(1.5)

if __name__ == "__main__":
    print(f"🛠️ Mode sélectionné : {MODE}")
    if FIXTURE_ID:
        print(f"🎯 Import unique pour fixture {FIXTURE_ID}")
        season_api = DEFAULT_SEASON
        season_str = format_season(season_api)
        insert_player_stats(FIXTURE_ID, season_str)
        insert_fixture_events(FIXTURE_ID)
    else:
        for league_id in LEAGUES:
            fetch_fixtures(league_id)

    conn.commit()
