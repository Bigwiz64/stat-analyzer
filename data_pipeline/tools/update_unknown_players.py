# data_pipeline/tools/update_unknown_players.py

import sqlite3
from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path
from data_pipeline.api_utils.utils_dates import get_api_season

def get_current_season():
    from datetime import datetime
    today = datetime.today()
    year = today.year
    return f"{year - 1}-{year}" if today.month < 7 else f"{year}-{year + 1}"

def update_unknown_players(verbose=True):
    DB_PATH = get_db_path()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Récupère tous les joueurs "Inconnu"
    cursor.execute("SELECT id FROM players WHERE name = 'Inconnu'")
    unknown_players = cursor.fetchall()

    season = get_current_season()
    if verbose:
        print(f"🔍 {len(unknown_players)} joueurs à mettre à jour pour la saison {season}...")

    updated = 0
    for (player_id,) in unknown_players:
        try:
            response = get_api_json("players", params={"id": player_id, "season": season}).get("response", [])
            if response:
                player_data = response[0]["player"]
                name = player_data["name"]
                position = player_data.get("position")
                nationality = player_data.get("nationality")

                cursor.execute("""
                    UPDATE players
                    SET name = ?, position = ?, country_flag = ?
                    WHERE id = ?
                """, (name, position, nationality, player_id))

                if verbose:
                    print(f"✅ {player_id} → {name} ({position}, {nationality})")
                updated += 1
            else:
                if verbose:
                    print(f"⚠️ Aucun retour API pour le joueur {player_id}")
        except Exception as e:
            print(f"❌ Erreur pour le joueur {player_id} : {e}")

    conn.commit()
    conn.close()

    if verbose:
        print(f"✅ Mise à jour terminée. {updated} joueurs mis à jour.")
