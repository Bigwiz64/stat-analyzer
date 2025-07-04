import sys
import os
import sqlite3
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# 🔁 Import chemins et API
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path
from app.data_access import repair_player_stats_from_events, fallback_player_stats_from_events
from data_pipeline.tools.update_unknown_players import update_unknown_players

# 🔐 Chargement .env
load_dotenv()

# 📍 Connexion à la base
DB_PATH = get_db_path()
print(f"\U0001F4C1 Base de données utilisée : {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def format_season(year):
    return f"{year}-{year + 1}"

def get_season_from_date(date_str, league_id):
    date_obj = datetime.strptime(date_str[:10], "%Y-%m-%d")
    year = date_obj.year
    month = date_obj.month
    if league_id in [103, 113, 244, 119]:  # Norvège, Suède, Finlande, Danemark
        return year
    return year if month >= 7 else year - 1

LEAGUES = [
    103, 113, 244, 71, 169, 239, 253
]

SEASON_BY_LEAGUE = {
    2: 2024, 3: 2024, 848: 2024, 136: 2024, 103: 2025, 113: 2025, 172: 2024,
    144: 2024, 95: 2024, 244: 2025, 119: 2024, 186: 2024, 188: 2025, 81: 2024,
    307: 2024, 128: 2025, 71: 2025, 265: 2025, 169: 2025, 318: 2024, 239: 2025,
    292: 2025, 210: 2024, 242: 2025, 329: 2025, 253: 2025, 197: 2024, 357: 2025,
    164: 2025, 98: 2025, 365: 2025, 262: 2024, 250: 2025, 106: 2024, 283: 2024,
    207: 2024, 203: 2024, 333: 2024, 239: 2025
}

DEFAULT_SEASON = 2024
FROM_DATE = sys.argv[1] if len(sys.argv) > 1 else "2025-06-01"
TO_DATE = sys.argv[2] if len(sys.argv) > 2 else "2025-07-03"
MODE = sys.argv[3] if len(sys.argv) > 3 else "complet"

def insert_player_stats(fixture_id, season_str):
    cursor.execute("SELECT COUNT(*) FROM player_stats WHERE fixture_id = ?", (fixture_id,))
    count = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(minutes), SUM(goals), SUM(assists) FROM player_stats WHERE fixture_id = ?", (fixture_id,))
    minutes_sum, goals_sum, assists_sum = cursor.fetchone()

    if count > 0 and (minutes_sum or 0) == 0 and (goals_sum or 0) == 0 and (assists_sum or 0) == 0:
        print(f"🔁 Réimport des stats joueurs pour match {fixture_id} (stats nulles)")
        cursor.execute("DELETE FROM player_stats WHERE fixture_id = ?", (fixture_id,))
    elif count > 0:
        print(f"✅ Stats joueurs déjà présentes pour match {fixture_id} — skip.")
        return

    try:
        stats_data = get_api_json("fixtures/players", params={"fixture": fixture_id}).get("response", [])
        if not stats_data:
            raise ValueError("⚠️ Aucun joueur retourné")

        for team_data in stats_data:
            team_id = team_data["team"]["id"]
            for entry in team_data["players"]:
                player = entry["player"]
                stats = entry["statistics"][0] if entry["statistics"] else {}

                cursor.execute("""
                    INSERT OR IGNORE INTO players (id, name, position)
                    VALUES (?, ?, ?)
                """, (
                    player["id"], player["name"], player.get("position", "")
                ))

                cursor.execute("""
                    INSERT OR REPLACE INTO player_stats (
                        player_id, fixture_id, team_id, minutes, goals, assists,
                        shots_total, shots_on_target, xg, xa,
                        penalty_scored, penalty_missed, yellow_cards, red_cards, season
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
        print("⛑️ Tentative de secours via les événements du match...")
        conn.commit()
        fallback_player_stats_from_events(fixture_id)

def insert_fixture_events(fixture_id):
    print(f"🔁 Réinsertion forcée des événements du match {fixture_id}")
    cursor.execute("DELETE FROM fixture_events WHERE fixture_id = ?", (fixture_id,))
    try:
        events_data = get_api_json("fixtures/events", params={"fixture": fixture_id}).get("response", [])
        for event in events_data:
            elapsed = event.get("time", {}).get("elapsed")
            extra = event.get("time", {}).get("extra") or 0
            minute = elapsed + extra if elapsed is not None else None
            team_id = event["team"]["id"]
            player_id = event.get("player", {}).get("id")
            assist_id = event.get("assist", {}).get("id")
            cursor.execute("""
                INSERT INTO fixture_events (
                    fixture_id, team_id, player_id, assist_id, type, detail, comments, elapsed, extra, minute
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fixture_id, team_id, player_id, assist_id,
                event["type"], event["detail"], event.get("comments"),
                elapsed, extra, minute
            ))
        conn.commit()
        print("✅ Événements insérés avec succès.")
    except Exception as e:
        print(f"❌ Erreur événements match {fixture_id} : {e}")

def insert_fixture(data, season_str, verbose=True):
    fixture = data["fixture"]
    league = data["league"]
    teams = data["teams"]
    goals = data["goals"]
    season_value = get_season_from_date(fixture["date"], league["id"])
    cursor.execute("SELECT home_goals, away_goals FROM fixtures WHERE id = ?", (fixture["id"],))
    result = cursor.fetchone()
    already_has_score = result and result[0] is not None and result[1] is not None
    if already_has_score and MODE == "rapide":
        if verbose:
            print(f"⏭️ Match {fixture['id']} déjà à jour.")
        insert_fixture_events(fixture["id"])
        insert_player_stats(fixture["id"], season_str)
        return
    cursor.execute("""
        INSERT OR REPLACE INTO fixtures (
            id, date, league_id, home_team_id, away_team_id, home_goals, away_goals, referee, season
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fixture["id"], fixture["date"], league["id"],
        teams["home"]["id"], teams["away"]["id"],
        goals["home"], goals["away"], fixture.get("referee"), season_value
    ))
    for side in ["home", "away"]:
        team = teams[side]
        cursor.execute("""
            INSERT OR IGNORE INTO teams (id, name, logo)
            VALUES (?, ?, ?)
        """, (team["id"], team["name"], team["logo"]))
    insert_player_stats(fixture["id"], season_str)
    insert_fixture_events(fixture["id"])
    repair_player_stats_from_events(fixture["id"])

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
        insert_fixture(fixture, season_str, verbose=(MODE == "complet"))
        total_added += 1
    print(f"✅ {total_added} matchs traités pour la ligue {league_id}")
    time.sleep(1.5)

def update_players_table(team_ids, api_key, season):
    print(f"🔍 {len(team_ids)} équipes à mettre à jour pour la saison {season}...")
    headers = {"X-RapidAPI-Key": api_key}
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        for team_id in team_ids:
            params = {
                "team": team_id,
                "season": int(str(season)[:4])  # Extrait 2024 de "2024-2025"
            }

            try:
                response = requests.get("https://v3.football.api-sports.io/players", headers=headers, params=params)
                data = response.json()

                if data.get("errors"):
                    print(f"❌ Erreur API : {data['errors']}")
                    continue

                for player in data["response"]:
                    p = player["player"]
                    player_id = p.get("id")
                    name = p.get("name")
                    firstname = p.get("firstname")
                    lastname = p.get("lastname")
                    age = p.get("age")
                    position = player.get("statistics", [{}])[0].get("games", {}).get("position")
                    nationality = p.get("nationality")
                    country_flag = p.get("nationality")  # Tu peux améliorer ça si besoin

                    cursor.execute("""
                        INSERT OR REPLACE INTO players (id, name, firstname, lastname, position, age, country, country_flag)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (player_id, name, firstname, lastname, position, age, nationality, country_flag))

                print(f"✅ Équipe {team_id} mise à jour")
            except Exception as e:
                print(f"❌ Erreur lors de la mise à jour de l'équipe {team_id} : {e}")

import requests

def update_unknown_players_info(api_key, season):
    print("🔍 Recherche des joueurs inconnus à mettre à jour...")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT p.id, ps.team_id
            FROM players p
            JOIN player_stats ps ON p.id = ps.player_id
            WHERE p.name = 'Inconnu'
        """)
        unknowns = cursor.fetchall()
    
    print(f"🧩 {len(unknowns)} joueurs inconnus à mettre à jour...")

    headers = {"X-RapidAPI-Key": api_key}
    for player_id, team_id in unknowns:
        try:
            params = {
                "team": team_id,
                "season": int(str(season)[:4])  # Extraire "2024" de "2024-2025"
            }
            res = requests.get("https://v3.football.api-sports.io/players", headers=headers, params=params)
            res_json = res.json()
            players_data = res_json.get("response", [])
            for player in players_data:
                p = player["player"]
                if p["id"] == player_id:
                    firstname = p.get("firstname")
                    lastname = p.get("lastname")
                    name = f"{firstname} {lastname}".strip()
                    age = p.get("age")
                    nationality = p.get("nationality")
                    position = player.get("statistics", [{}])[0].get("games", {}).get("position", "?")
                    flag = p.get("photo")

                    with sqlite3.connect(DB_PATH) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE players
                            SET name = ?, position = ?, age = ?, country = ?, country_flag = ?
                            WHERE id = ?
                        """, (name, position, age, nationality, flag, player_id))
                    print(f"✅ Joueur {name} mis à jour")
        except Exception as e:
            print(f"❌ Erreur pour le joueur {player_id} : {e}")

if __name__ == "__main__":
    print(f"🛠️ Mode sélectionné : {MODE}")
    for league_id in LEAGUES:
        fetch_fixtures(league_id)
    conn.commit()

    print("\n📊 Vérification des saisons insérées :")
    cursor.execute("SELECT DISTINCT season FROM fixtures ORDER BY season DESC")
    seasons = cursor.fetchall()
    for season in seasons:
        print(" - Saison :", season[0])

    # ✅ Mise à jour des joueurs inconnus avec saison dynamique
    print("\n🔍 Recherche des joueurs inconnus à mettre à jour...")
    API_KEY = os.getenv("API_SPORT_KEY")
    target_season = sys.argv[4] if len(sys.argv) > 4 else "2025-2026"
    print(f"📅 Saison utilisée pour mise à jour des joueurs : {target_season}")
    update_unknown_players()


