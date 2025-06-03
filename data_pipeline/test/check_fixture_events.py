import sqlite3
import os

# 🔧 Chemin absolu vers la base (à adapter si besoin)
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db", "data.db"))

# 🆔 ID du match à tester
fixture_id = 1224237

# 📋 Connexion à la base et récupération des événements
with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.elapsed, e.extra, p.name AS player, a.name AS assist, e.type, e.detail, e.comments
        FROM fixture_events e
        LEFT JOIN players p ON e.player_id = p.id
        LEFT JOIN players a ON e.assist_id = a.id
        WHERE e.fixture_id = ?
        ORDER BY e.elapsed, e.extra
    """, (fixture_id,))
    events = cursor.fetchall()

# 🖨️ Affichage formaté
if not events:
    print("❌ Aucun événement trouvé pour ce match.")
else:
    print(f"📋 {len(events)} événements pour le match {fixture_id} :\n")
    for e in events:
        minute = f"{e[0]}'" + (f"+{e[1]}" if e[1] else "")
        player = e[2] or "❓"
        assist = f" (assisté par {e[3]})" if e[3] else ""
        event_type = e[4] or "?"
        detail = e[5] or ""
        comments = f" – {e[6]}" if e[6] else ""
        print(f"{minute:<6} | {event_type:<8} - {detail:<15} | {player}{assist}{comments}")
