import os
import sys
import sqlite3

# 🔁 Ajout du chemin racine pour importer get_db_path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()

FIXTURE_ID = 1214008  # Saint-Étienne vs Lyon
PLAYER_ID = 1214030   # Lucas Stassin

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()

    # 1. Affiche les matchs du 20 avril 2025
    cursor.execute("""
        SELECT f.id, f.date, t1.name AS home_team, t2.name AS away_team, l.name AS league
        FROM fixtures f
        JOIN teams t1 ON f.home_team_id = t1.id
        JOIN teams t2 ON f.away_team_id = t2.id
        JOIN leagues l ON f.league_id = l.id
        WHERE DATE(f.date) = '2025-04-20'
    """)

    rows = cursor.fetchall()
    print("📅 Matchs joués le 20/04/2025 :\n")
    for row in rows:
        fixture_id, date, home, away, league = row
        print(f"🆔 {fixture_id} | {home} vs {away} | {league} | {date}")

    # 2. Vérifie les stats du joueur
    print(f"\n📊 Statistiques de Lucas Stassin dans le match {FIXTURE_ID} :")
    cursor.execute("""
        SELECT goals, assists, minutes, team_id
        FROM player_stats
        WHERE fixture_id = ? AND player_id = ?
    """, (FIXTURE_ID, PLAYER_ID))
    stats = cursor.fetchone()
    if stats:
        print(f"✅ Goals: {stats[0]}, Assists: {stats[1]}, Minutes: {stats[2]}, Team ID: {stats[3]}")
    else:
        print("❌ Aucune ligne trouvée dans player_stats.")

    # 3. Vérifie les événements du joueur
    print(f"\n📅 Événements enregistrés pour Lucas Stassin dans fixture_events :")
    cursor.execute("""
        SELECT type, detail, elapsed, extra, comments
        FROM fixture_events
        WHERE fixture_id = ? AND player_id = ?
    """, (FIXTURE_ID, PLAYER_ID))
    events = cursor.fetchall()
    if events:
        for e in events:
            print(f" - {e[0]} | {e[1]} à la {e[2]}+{e[3]} | Commentaire : {e[4]}")
    else:
        print("❌ Aucun événement trouvé dans fixture_events.")
