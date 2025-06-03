import sqlite3
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from data_pipeline.api_utils.path_utils import get_db_path

DB_PATH = get_db_path()
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print(f"📁 Base utilisée : {DB_PATH}")

# 1. Suppression des événements dupliqués exacts
print("🧼 Suppression des événements dupliqués...")
cursor.execute("""
    DELETE FROM fixture_events
    WHERE rowid NOT IN (
        SELECT MIN(rowid)
        FROM fixture_events
        GROUP BY fixture_id, team_id, player_id, assist_id, type, detail, minute
    )
""")
conn.commit()
print("✅ Événements dupliqués supprimés.")

# 2. Suppression des événements avec minute NULL
print("🧼 Suppression des événements sans minute...")
cursor.execute("DELETE FROM fixture_events WHERE minute IS NULL")
conn.commit()
print("✅ Événements sans minute supprimés.")

# 3. Suppression des événements sans type
print("🧼 Suppression des événements sans type...")
cursor.execute("DELETE FROM fixture_events WHERE type IS NULL OR TRIM(type) = ''")
conn.commit()
print("✅ Événements sans type supprimés.")

# 4. Vérification manuelle des goals où le buteur semble incorrect
print("🔍 Vérification des incohérences de buteur...")
cursor.execute("""
    SELECT fixture_id, player_id, assist_id, COUNT(*) 
    FROM fixture_events 
    WHERE type = 'Goal' AND detail = 'Normal Goal'
    GROUP BY fixture_id, player_id, assist_id 
    HAVING COUNT(*) > 1
""")
suspicious = cursor.fetchall()

if suspicious:
    print(f"❗ {len(suspicious)} événements suspects à vérifier (potentiel conflit buteur/assistant) :")
    for row in suspicious:
        print(" - fixture_id:", row[0], "| joueur:", row[1], "| assist:", row[2])
else:
    print("✅ Aucun conflit évident détecté dans les événements Goal.")

conn.close()
print("🎉 Nettoyage terminé.")
