import sqlite3

leagues = [
    (61, "Ligue 1"),
    (62, "Ligue 2"),
    (39, "Premier League"),
    (140, "La Liga"),
    (141, "La Liga 2"),
    (78, "Bundesliga"),
    (79, "2. Bundesliga"),
    (135, "Serie A"),
    (88, "Eredivisie"),
    (94, "Primeira Liga"),
    (203, "Super Lig"),
    (179, "Premiership (Écosse)"),
    (130, "A-League"),
    (40, "Championship")
]

conn = sqlite3.connect("data.db")
cursor = conn.cursor()

cursor.executemany("INSERT OR IGNORE INTO leagues (id, name) VALUES (?, ?)", leagues)

conn.commit()
conn.close()
