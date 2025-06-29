import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path
# ... le reste de ton code
import sqlite3

def import_missing_player_stats(fixture_id):
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    response = get_api_json('fixtures/players', params={'fixture': fixture_id})
    players_data = response.get('response', [])

    for team_data in players_data:
        team = team_data.get('team', {})
        players = team_data.get('players', [])

        for player_data in players:
            player = player_data.get('player', {})
            stats = player_data.get('statistics', [{}])[0]

            cursor.execute("""
                INSERT INTO player_stats (fixture_id, player_id, team_id, minutes, goals, assists, yellow, red)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fixture_id,
                player.get('id'),
                team.get('id'),
                stats.get('games', {}).get('minutes'),
                stats.get('goals', {}).get('total'),
                stats.get('goals', {}).get('assists'),
                stats.get('cards', {}).get('yellow'),
                stats.get('cards', {}).get('red'),
            ))

    conn.commit()
    conn.close()
    print(f"✅ Import terminé pour fixture {fixture_id}.")

import_missing_player_stats(1332775)
