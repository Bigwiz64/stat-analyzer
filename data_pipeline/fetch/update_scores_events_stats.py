## Tous les matchs à partir d'une date
#python3 update_scores_events_stats.py --from 2024-09-01

# Tous les matchs jusqu'à une date
#python3 update_scores_events_stats.py --to 2024-10-01

# Entre deux dates
#python3 update_scores_events_stats.py --from 2024-09-01 --to 2024-09-30

import os
import sys
import sqlite3
import time
from dotenv import load_dotenv
import argparse
from datetime import datetime


# 🔧 Ajout du chemin vers data_pipeline
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path

# 🔐 Chargement env + base
load_dotenv()
DB_PATH = get_db_path()

def update_score(fixture_id):
    response = get_api_json("fixtures", params={"id": fixture_id})
    fixture = response.get("response", [None])[0]

    if not fixture:
        print(f"❌ Match {fixture_id} introuvable.")
        return

    home_goals = fixture["goals"]["home"]
    away_goals = fixture["goals"]["away"]

    if home_goals is not None and away_goals is not None:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE fixtures
                SET home_goals = ?, away_goals = ?
                WHERE id = ?
            """, (home_goals, away_goals, fixture_id))
            conn.commit()
        print(f"✅ Score mis à jour : {home_goals} - {away_goals}")
    else:
        print("⏳ Score non encore disponible.")

def update_events(fixture_id):
    print(f"🔄 Événements pour match {fixture_id}")
    events = get_api_json("fixtures/events", params={"fixture": fixture_id}).get("response", [])

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fixture_events WHERE fixture_id = ?", (fixture_id,))
        for e in events:
            elapsed = e.get("time", {}).get("elapsed")
            extra = e.get("time", {}).get("extra") or 0
            minute = (elapsed or 0) + (extra or 0)

            cursor.execute("""
                INSERT INTO fixture_events (
                    fixture_id, team_id, player_id, assist_id, type, detail,
                    comments, elapsed, extra, minute
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fixture_id,
                e["team"]["id"],
                e.get("player", {}).get("id"),
                e.get("assist", {}).get("id"),
                e["type"],
                e["detail"],
                e.get("comments"),
                elapsed,
                extra,
                minute
            ))
        conn.commit()
    print(f"✅ {len(events)} événements insérés.")

def update_player_stats(fixture_id, season_str="2024-2025"):
    print(f"🔄 Stats joueurs pour match {fixture_id}")
    stats_data = get_api_json("fixtures/players", params={"fixture": fixture_id}).get("response", [])

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM player_stats WHERE fixture_id = ?", (fixture_id,))
        for team_data in stats_data:
            team_id = team_data["team"]["id"]
            for entry in team_data["players"]:
                player = entry["player"]
                stats = entry["statistics"][0] if entry["statistics"] else {}

                cursor.execute("""
                    INSERT OR IGNORE INTO players (id, name, position)
                    VALUES (?, ?, ?)
                """, (
                    player["id"],
                    player["name"],
                    player.get("position", "")
                ))

                cursor.execute("""
                    INSERT INTO player_stats (
                        player_id, fixture_id, team_id, minutes, goals, assists,
                        shots_total, shots_on_target, xg, xa,
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
                    season_str
                ))
        conn.commit()
    print(f"✅ Stats joueurs insérées.")

def main():
    parser = argparse.ArgumentParser(description="Met à jour scores, événements et stats joueurs.")
    parser.add_argument("--from", dest="from_date", help="Date de début (YYYY-MM-DD)", default=None)
    parser.add_argument("--to", dest="to_date", help="Date de fin (YYYY-MM-DD)", default=None)
    args = parser.parse_args()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        query = "SELECT id, date FROM fixtures WHERE home_goals IS NULL OR away_goals IS NULL"
        cursor.execute(query)
        all_fixtures = cursor.fetchall()

    filtered_fixtures = []
    for fixture_id, fixture_date in all_fixtures:
        if args.from_date and fixture_date < args.from_date:
            continue
        if args.to_date and fixture_date > args.to_date:
            continue
        filtered_fixtures.append((fixture_id, fixture_date))

    print(f"🔍 {len(filtered_fixtures)} matchs à mettre à jour.")

    for (fixture_id, _) in filtered_fixtures:
        update_score(fixture_id)
        update_events(fixture_id)
        update_player_stats(fixture_id)
        time.sleep(1.5)

    print("\n🎉 Mise à jour complète terminée.")

if __name__ == "__main__":
    main()
