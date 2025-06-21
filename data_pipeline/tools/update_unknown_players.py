# data_pipeline/tools/update_unknown_players.py

import sqlite3
import os
import csv
from data_pipeline.api_utils.utils_api import get_api_json
from data_pipeline.api_utils.path_utils import get_db_path
from data_pipeline.api_utils.utils_dates import get_api_season

def get_current_season_int():
    from datetime import datetime
    today = datetime.today()
    year = today.year
    return year if today.month >= 7 else year - 1

def update_unknown_players(verbose=True):
    DB_PATH = get_db_path()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Récupère tous les joueurs "Inconnu"
    cursor.execute("SELECT id FROM players WHERE name = 'Inconnu'")
    unknown_players = cursor.fetchall()

    season = get_current_season_int()
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

    # 🔽 Export CSV pour les joueurs toujours inconnus
    if verbose:
        print("\n🔍 Recherche des joueurs inconnus restants...")

    cursor.execute("""
        SELECT p.id AS player_id,
               fe.fixture_id,
               fe.team_id,
               t.name AS team_name,
               fe.type AS event_type
        FROM players p
        LEFT JOIN fixture_events fe ON p.id = fe.player_id
        LEFT JOIN teams t ON fe.team_id = t.id
        WHERE p.name = 'Inconnu'
        GROUP BY p.id
    """)
    remaining = cursor.fetchall()

    if remaining:
        output_dir = "exports"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"unknown_players_full_{season}.csv")

        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "player_id", "fixture_id", "team_id", "team_name",
                "event_type", "position", "new_name", "nationality"
            ])
            for row in remaining:
                writer.writerow(list(row) + ["", "", ""])  # Ajout colonnes manuelles vides

        print(f"📄 Export CSV enrichi : {output_file} ({len(remaining)} joueurs)")
    else:
        print("✅ Aucun joueur 'Inconnu' restant.")

    conn.close()

    if verbose:
        print(f"\n✅ Mise à jour terminée. {updated} joueurs mis à jour.")

