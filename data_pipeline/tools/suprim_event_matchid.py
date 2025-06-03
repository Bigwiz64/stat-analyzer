import sys
import os
import sqlite3

# 🔁 Ajoute le chemin à la racine du projet
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 📁 Fichier : data_pipeline/tools/reset_imported_data.py

from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ❗️ Tables à nettoyer sans supprimer le contenu statique (logos ligues, joueurs)
tables_to_clean = [
    "fixture_events",
    "player_stats",
    "fixtures"
]

print("🧹 Suppression des données importées par import_fixtures_2024...\n")

for table in tables_to_clean:
    try:
        cursor.execute(f"DELETE FROM {table}")
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        print(f"✅ Données supprimées : {table}")
    except Exception as e:
        print(f"❌ Erreur avec {table} : {e}")

conn.commit()
conn.close()
print("\n✅ Nettoyage terminé. Les équipes, ligues, joueurs sont conservés.")

