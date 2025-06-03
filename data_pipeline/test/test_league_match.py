import sys, os, sqlite3
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from data_pipeline.api_utils.path_utils import get_db_path

db_path = get_db_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Change "Norvège" par "Chine", "Espagne", etc. si besoin
country = "Norvège"
cursor.execute("""
    SELECT f.id, f.date, t1.name, t2.name
    FROM fixtures f
    JOIN leagues l ON f.league_id = l.id
    JOIN teams t1 ON f.home_team_id = t1.id
    JOIN teams t2 ON f.away_team_id = t2.id
    WHERE l.country = ?
    ORDER BY f.date DESC
    LIMIT 10
""", (country,))
rows = cursor.fetchall()

print(f"📊 {len(rows)} matchs trouvés pour {country}")
for r in rows:
    print(f"{r[1]} : {r[2]} vs {r[3]}")
