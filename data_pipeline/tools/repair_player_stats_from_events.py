import sqlite3
from collections import defaultdict
import os

# Remplace ceci par le chemin absolu vers ta base si besoin
DB_PATH = "/Users/morane/stat-analyzer/data_pipeline/db/data.db"


conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT DISTINCT fixture_id FROM fixture_events")
fixture_ids = [row[0] for row in cursor.fetchall()]

updated = 0
skipped = 0

for fixture_id in fixture_ids:
    cursor.execute("""
        SELECT type, player_id, assist_id, team_id
        FROM fixture_events
        WHERE fixture_id = ?
          AND type = 'Goal'
    """, (fixture_id,))
    rows = cursor.fetchall()

    if not rows:
        skipped += 1
        continue

    cursor.execute("DELETE FROM player_stats WHERE fixture_id = ?", (fixture_id,))

    player_stats = defaultdict(lambda: {
        "fixture_id": fixture_id,
        "team_id": None,
        "goals": 0,
        "assists": 0,
        "minutes": 90
    })

    for row in rows:
        type_, player_id, assist_id, team_id = row
        if player_id:
            player_stats[player_id]["goals"] += 1
            player_stats[player_id]["team_id"] = team_id
        if assist_id:
            player_stats[assist_id]["assists"] += 1
            player_stats[assist_id]["team_id"] = team_id

    for player_id, stats in player_stats.items():
        cursor.execute("""
            INSERT INTO player_stats (player_id, fixture_id, team_id, goals, assists, minutes, season)
            VALUES (?, ?, ?, ?, ?, ?, (
                SELECT season FROM fixtures WHERE id = ?
            ))
        """, (
            player_id, stats["fixture_id"], stats["team_id"],
            stats["goals"], stats["assists"], stats["minutes"], fixture_id
        ))

    updated += 1

conn.commit()
conn.close()

print(f"✅ Total matches traités : {len(fixture_ids)}")
print(f"🟢 Statistiques recalculées : {updated}")
print(f"⚪ Matches ignorés (sans but) : {skipped}")
