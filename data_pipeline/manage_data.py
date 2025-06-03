import argparse
import sqlite3
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


import time
from dotenv import load_dotenv
from data_pipeline.api_utils.utils_api import get_api_json, call_api
from data_pipeline.api_utils.path_utils import get_db_path
import json

load_dotenv()
DB_PATH = get_db_path()


def update_scores():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM fixtures WHERE home_goals IS NULL OR away_goals IS NULL")
        fixtures = cursor.fetchall()

    print(f"\n\u26a1 Mise à jour de {len(fixtures)} matchs sans score...")
    for (fixture_id,) in fixtures:
        response = call_api("fixtures", params={"id": fixture_id})
        if response and response.get("response"):
            fixture = response["response"][0]
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
                print(f"✅ Match {fixture_id} mis à jour : {home_goals} - {away_goals}")
            else:
                print(f"⏳ Match {fixture_id} non terminé ou score indisponible.")
        time.sleep(1)


def fetch_and_print_events(fixture_id):
    response = get_api_json("fixtures/events", params={"fixture": fixture_id})
    events = response.get("response", [])
    print(f"\n🎯 {len(events)} événements récupérés pour le match {fixture_id} :\n")
    print(json.dumps(events, indent=2))


def fetch_league_fixtures(league_id, season, from_date, to_date):
    print(f"\n📦 Récupération Ligue {league_id} | Saison {season} | {from_date} → {to_date}")
    res = get_api_json("fixtures", params={
        "league": league_id,
        "season": season,
        "from": from_date,
        "to": to_date
    })
    fixtures = res.get("response", [])
    print(f"✅ {len(fixtures)} match(s) reçu(s)")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        for fixture in fixtures:
            f = fixture["fixture"]
            l = fixture["league"]
            t = fixture["teams"]
            g = fixture["goals"]
            fixture_id = f["id"]

            cursor.execute("""
                INSERT OR REPLACE INTO fixtures (id, date, league_id, home_team_id, away_team_id, home_goals, away_goals, referee)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fixture_id, f["date"], l["id"], t["home"]["id"], t["away"]["id"],
                g["home"], g["away"], f.get("referee")
            ))

            for side in ["home", "away"]:
                team = t[side]
                cursor.execute("""
                    INSERT OR IGNORE INTO teams (id, name, logo)
                    VALUES (?, ?, ?)
                """, (team["id"], team["name"], team["logo"]))

            # Récupération des stats joueurs
            stats_data = get_api_json("fixtures/players", params={"fixture": fixture_id}).get("response", [])
            for team_data in stats_data:
                team_id = team_data["team"]["id"]
                for entry in team_data["players"]:
                    player = entry["player"]
                    stats = entry["statistics"][0] if entry["statistics"] else {}
                    cursor.execute("""
                        INSERT OR IGNORE INTO players (id, name, position)
                        VALUES (?, ?, ?)
                    """, (player["id"], player["name"], player.get("position", "")))

                    cursor.execute("""
                        INSERT OR REPLACE INTO player_stats (player_id, fixture_id, team_id, minutes, goals, assists)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        player["id"], fixture_id, team_id,
                        stats.get("games", {}).get("minutes", 0),
                        stats.get("goals", {}).get("total", 0),
                        stats.get("goals", {}).get("assists", 0)
                    ))

            # Récupération des événements
            events_data = get_api_json("fixtures/events", params={"fixture": fixture_id}).get("response", [])
            cursor.execute("DELETE FROM fixture_events WHERE fixture_id = ?", (fixture_id,))

            for event in events_data:
                elapsed = event.get("time", {}).get("elapsed")
                extra = event.get("time", {}).get("extra") or 0
                minute = elapsed + extra if elapsed is not None else None

                team_id = event["team"]["id"]
                player_id = event.get("player", {}).get("id")
                assist_id = event.get("assist", {}).get("id")
                cursor.execute("""
                    INSERT INTO fixture_events (fixture_id, team_id, player_id, assist_id, type, detail, comments, elapsed, extra, minute)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fixture_id, team_id, player_id, assist_id,
                    event["type"], event["detail"], event.get("comments"),
                    elapsed, extra, minute
                ))
        conn.commit()


def update_league_logos():
    import requests
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM leagues")
        league_ids = [row[0] for row in cursor.fetchall()]

        for league_id in league_ids:
            res = requests.get(
                "https://v3.football.api-sports.io/leagues",
                headers={"x-apisports-key": os.getenv("API_SPORT_KEY")},
                params={"id": league_id}
            )
            data = res.json()
            if data["response"]:
                league_info = data["response"][0]
                logo = league_info["league"]["logo"]
                flag = league_info["country"].get("flag", "")

                cursor.execute("""
                    UPDATE leagues SET logo = ?, flag = ? WHERE id = ?
                """, (logo, flag, league_id))
                print(f"✅ Ligue {league_id} mise à jour avec logo + drapeau.")
            else:
                print(f"⚠️ Aucune donnée pour la ligue {league_id}.")
        conn.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🛠️ Outil de gestion de données football")
    parser.add_argument("--task", required=True, choices=["import", "update_scores", "debug_match", "fetch_logos"], help="Tâche à exécuter")
    parser.add_argument("--league", type=int, help="ID de la ligue")
    parser.add_argument("--season", type=int, help="Année de la saison (ex: 2024)")
    parser.add_argument("--from", dest="from_date", help="Date de début au format YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", help="Date de fin au format YYYY-MM-DD")
    parser.add_argument("--id", type=int, help="ID du match pour debug")

    args = parser.parse_args()

    if args.task == "update_scores":
        update_scores()

    elif args.task == "debug_match" and args.id:
        fetch_and_print_events(args.id)

    elif args.task == "fetch_logos":
        update_league_logos()

    elif args.task == "import":
        if not all([args.league, args.season, args.from_date, args.to_date]):
            print("❌ Pour importer, tu dois fournir --league, --season, --from et --to")
        else:
            fetch_league_fixtures(args.league, args.season, args.from_date, args.to_date)

    else:
        print("❌ Paramètres invalides ou incomplets.")
