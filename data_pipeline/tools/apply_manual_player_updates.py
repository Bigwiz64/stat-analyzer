# data_pipeline/tools/apply_manual_player_updates.py

import sqlite3
import csv
import os
from data_pipeline.api_utils.path_utils import get_db_path

def apply_manual_player_updates(csv_filename="exports/unknown_players_full_2025.csv", verbose=True):
    if not os.path.exists(csv_filename):
        print(f"❌ Fichier CSV non trouvé : {csv_filename}")
        return

    DB_PATH = get_db_path()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updated = 0
    with open(csv_filename, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            player_id = row["player_id"]
            new_name = row["new_name"].strip()
            new_position = row["position"].strip()
            new_country = row["nationality"].strip()

            if not new_name:  # Pas de mise à jour si le nom n'est pas rempli
                continue

            cursor.execute("""
                UPDATE players
                SET name = ?, position = ?, country_flag = ?
                WHERE id = ?
            """, (new_name, new_position or None, new_country or None, player_id))

            if verbose:
                print(f"📝 Joueur {player_id} → {new_name} ({new_position}, {new_country})")
            updated += 1

    conn.commit()
    conn.close()

    print(f"\n✅ {updated} joueurs mis à jour depuis {csv_filename}")

if __name__ == "__main__":
    apply_manual_player_updates()
