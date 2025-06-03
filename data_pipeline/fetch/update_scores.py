import os
import sqlite3
import time
from dotenv import load_dotenv
from data_pipeline.api_utils.utils_api import call_api
from data_pipeline.api_utils.path_utils import get_db_path

# 🔐 Chargement de la base et de l’environnement
load_dotenv()
DB_PATH = get_db_path()

# ================================
# 🔄 Mise à jour du score d’un match
# ================================
def update_fixture_score(fixture_id):
    response = call_api("fixtures", params={"id": fixture_id})

    if not response or not response.get("response"):
        print(f"❌ Aucun match trouvé avec l'ID {fixture_id}")
        return

    fixture = response["response"][0]
    home_goals = fixture["goals"]["home"]
    away_goals = fixture["goals"]["away"]

    if home_goals is not None and away_goals is not None:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE fixtures
                SET home_goals = ?, away_goals = ?
                WHERE id = ?
            """, (home_goals, away_goals, fixture_id))
            conn.commit()
        print(f"✅ Match {fixture_id} mis à jour : {home_goals} - {away_goals}")
    else:
        print(f"⏳ Match {fixture_id} non terminé ou score indisponible.")

# ================================
# 🔁 Traitement de tous les matchs sans score
# ================================
def main():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM fixtures WHERE home_goals IS NULL OR away_goals IS NULL")
        fixtures = cursor.fetchall()

    print(f"🔎 {len(fixtures)} matchs à mettre à jour...\n")

    for (fixture_id,) in fixtures:
        update_fixture_score(fixture_id)
        time.sleep(1)  # Pause API

    print("\n🎉 Tous les scores ont été mis à jour.")

# ================================
# 🟢 Exécution
# ================================
if __name__ == "__main__":
    main()
