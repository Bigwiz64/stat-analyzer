import sqlite3
from data_pipeline.api_utils.path_utils import get_db_path

def generate_missing_player_stats_from_events():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Chercher tous les fixtures ayant des events mais aucun player_stats
    cursor.execute("""
        SELECT DISTINCT fixture_id 
        FROM fixture_events
        WHERE fixture_id NOT IN (SELECT DISTINCT fixture_id FROM player_stats)
    """)
    fixtures_missing_stats = cursor.fetchall()

    print(f"🔍 {len(fixtures_missing_stats)} matchs sans player_stats mais avec events trouvés.\n")

    for (fixture_id,) in fixtures_missing_stats:
        print(f"▶️ Traitement du fixture {fixture_id}...")

        # Récupérer les joueurs impliqués dans des events
        cursor.execute("""
            SELECT DISTINCT player_id, team_id 
            FROM fixture_events
            WHERE fixture_id = ? AND player_id IS NOT NULL
        """, (fixture_id,))
        players = cursor.fetchall()

        print(f"   → {len(players)} joueurs impliqués dans des events.")

        for player_id, team_id in players:
            # Compter les buts et les passes décisives (les passes ne sont pas forcément bien détectables ici mais on garde)
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN type = 'Goal' THEN 1 ELSE 0 END) AS goals
                FROM fixture_events
                WHERE fixture_id = ? AND player_id = ?
            """, (fixture_id, player_id))
            stats = cursor.fetchone()
            goals = stats[0] or 0

            # On ne peut pas détecter les assists proprement ici car pas de champ "Assist" direct dans les events
            assists = 0  # Tu pourras améliorer plus tard en analysant les assist_id si tu veux

            cursor.execute("""
                INSERT INTO player_stats (fixture_id, player_id, team_id, minutes, goals, assists)
                VALUES (?, ?, ?, NULL, ?, ?)
            """, (
                fixture_id,
                player_id,
                team_id,
                goals,
                assists
            ))

            print(f"     ✅ Joueur {player_id} | Buts: {goals}")

    conn.commit()
    conn.close()
    print("\n✅ Import terminé. Les données manquantes ont été générées à partir des events.")

if __name__ == "__main__":
    generate_missing_player_stats_from_events()
