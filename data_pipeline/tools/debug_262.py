import sqlite3
import os
import sys

# Ajouter le chemin du projet à PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()
LEAGUE_ID = 262

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()

    # 🔍 1. Vérifie le nombre de matchs pour la ligue 242
    cursor.execute("SELECT COUNT(*) FROM fixtures WHERE league_id = ?", (LEAGUE_ID,))
    match_count = cursor.fetchone()[0]
    print(f"✅ {match_count} matchs trouvés pour la ligue {LEAGUE_ID}")

    # 🔍 2. Vérifie les ID des équipes utilisées dans les matchs
    cursor.execute("""
        SELECT DISTINCT home_team_id FROM fixtures WHERE league_id = ?
        UNION
        SELECT DISTINCT away_team_id FROM fixtures WHERE league_id = ?
    """, (LEAGUE_ID, LEAGUE_ID))
    team_ids_in_fixtures = [row[0] for row in cursor.fetchall()]
    print(f"🔍 {len(team_ids_in_fixtures)} équipes distinctes dans les matchs")

    # 🔍 3. Vérifie quelles équipes sont manquantes dans la table `teams`
    placeholders = ",".join(["?"] * len(team_ids_in_fixtures))
    cursor.execute(f"SELECT id FROM teams WHERE id IN ({placeholders})", team_ids_in_fixtures)
    existing_team_ids = set(row[0] for row in cursor.fetchall())

    missing_team_ids = [tid for tid in team_ids_in_fixtures if tid not in existing_team_ids]
    if missing_team_ids:
        print(f"❌ {len(missing_team_ids)} équipes manquantes dans la table teams : {missing_team_ids}")
    else:
        print("✅ Toutes les équipes des matchs sont présentes dans la table teams")

    # 🔍 4. Optionnel : Affiche les ligues avec leur logo pour contrôle
    cursor.execute("SELECT id, name, country, logo, flag FROM leagues WHERE id = ?", (LEAGUE_ID,))
    league = cursor.fetchone()
    if league:
        print(f"📘 Ligue {league[0]} : {league[1]} ({league[2]})")
        print(f"   Logo: {league[3]}")
        print(f"   Drapeau: {league[4]}")
    else:
        print("⚠️ Ligue non trouvée dans la table leagues")
