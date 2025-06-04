import sqlite3
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path
from data_pipeline.api_utils.utils_dates import get_api_season
season = get_api_season()


# Connexion à la base de données
DB_PATH = get_db_path()
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Récupère tous les joueurs nommés "Inconnu"
cursor.execute("SELECT id FROM players WHERE name = 'Inconnu'")
unknown_players = cursor.fetchall()

# Saison actuelle
season = get_api_season()

print(f"🔍 {len(unknown_players)} joueurs à mettre à jour pour la saison {season}...")

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

            print(f"✅ Joueur {player_id} mis à jour : {name} ({position}, {nationality})")
        else:
            print(f"⚠️ Aucun retour API pour le joueur {player_id}")
    except Exception as e:
        print(f"❌ Erreur pour le joueur {player_id} : {e}")

conn.commit()
conn.close()
print("✅ Mise à jour terminée.")