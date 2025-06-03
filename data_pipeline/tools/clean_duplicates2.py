import sqlite3
import os

# Connexion à la base
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("🧹 Nettoyage des doublons...")

# Supprimer les doublons dans player_stats (garder la ligne avec le plus de minutes jouées)
cursor.execute("""
    DELETE FROM player_stats
    WHERE rowid NOT IN (
        SELECT MAX(rowid)
        FROM player_stats
        GROUP BY player_id, fixture_id
    )
""")
print("✅ Doublons supprimés dans player_stats")

# Optionnel : suppression des joueurs non utilisés
cursor.execute("""
    DELETE FROM players
    WHERE id NOT IN (
        SELECT DISTINCT player_id FROM player_stats
    )
""")
print("✅ Joueurs orphelins supprimés")

conn.commit()
conn.close()
print("🎉 Nettoyage terminé.")
