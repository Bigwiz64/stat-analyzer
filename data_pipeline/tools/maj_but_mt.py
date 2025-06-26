import sqlite3
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from data_pipeline.api_utils.path_utils import get_db_path

def update_half_time_goals():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # Récupère tous les matches
    cursor.execute("SELECT id, home_team_id, away_team_id FROM fixtures")
    fixtures = cursor.fetchall()

    for fixture_id, home_team_id, away_team_id in fixtures:
        # Compter les buts en 1ère mi-temps (<= 45ème minute)
        cursor.execute("""
            SELECT team_id, COUNT(*) FROM fixture_events
            WHERE fixture_id = ?
            AND type = 'Goal'
            AND minute <= 45
            GROUP BY team_id
        """, (fixture_id,))
        ht_goals = {team_id: count for team_id, count in cursor.fetchall()}

        home_goals_ht = ht_goals.get(home_team_id, 0)
        away_goals_ht = ht_goals.get(away_team_id, 0)

        cursor.execute("""
            UPDATE fixtures
            SET home_goals_ht = ?, away_goals_ht = ?
            WHERE id = ?
        """, (home_goals_ht, away_goals_ht, fixture_id))

    conn.commit()
    conn.close()
    print("✅ Mise à jour des buts en 1ère mi-temps terminée.")

if __name__ == "__main__":
    update_half_time_goals()
