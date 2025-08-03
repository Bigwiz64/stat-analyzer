
import sqlite3
import os
from data_pipeline.api_utils.path_utils import get_db_path
from data_pipeline.api_utils.utils_dates import get_season_from_date
from app.utils import get_position_abbr, get_team_abbr
from datetime import datetime



DB_PATH = get_db_path()


def get_all_fixtures():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fixtures.id, fixtures.date, teams_home.name, teams_away.name, fixtures.home_goals, fixtures.away_goals
            FROM fixtures
            JOIN teams AS teams_home ON fixtures.home_team_id = teams_home.id
            JOIN teams AS teams_away ON fixtures.away_team_id = teams_away.id
            ORDER BY fixtures.date DESC
        """)
        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "date": row[1][:10],
            "home_team": row[2],
            "away_team": row[3],
            "score": f"{row[4]} - {row[5]}"
        }
        for row in rows
    ]

def get_season_for_fixture(date_str, league_id):
    from datetime import datetime
    date_obj = datetime.strptime(date_str[:10], "%Y-%m-%d")
    year = date_obj.year
    month = date_obj.month

    # Ligues qui jouent sur l’année civile (printemps → automne)
    leagues_calendar_year = [103, 113, 244, 119]  # Norvège, Suède, Finlande, Danemark

    if league_id in leagues_calendar_year:
        return year

    # Autres ligues : saison classique été → printemps
    return year if month >= 7 else year - 1


def get_match_with_cumulative_player_stats(fixture_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 1. Récupération des infos du match
        cursor.execute("""
            SELECT f.id, f.date, f.home_team_id, f.away_team_id, f.league_id,
                   t1.name, t2.name, f.home_goals, f.away_goals
            FROM fixtures f
            JOIN teams t1 ON f.home_team_id = t1.id
            JOIN teams t2 ON f.away_team_id = t2.id
            WHERE f.id = ?
        """, (fixture_id,))
        match = cursor.fetchone()

        if not match:
            print("❌ Match non trouvé :", fixture_id)
            return None

        match_date = match[1]
        league_id = match[4]
        season = get_season_for_fixture(match_date, league_id)
        home_team_id = match[2]
        away_team_id = match[3]

        match_data = {
            "id": match[0],
            "date": match_date[:10],
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "league_id": league_id,
            "home_team": match[5],
            "away_team": match[6],
            "home_goals": match[7],
            "away_goals": match[8],
            "home_players": [],
            "away_players": [],
        }

        print("📦 Stats cumulées pour match :", fixture_id)
        print(f"🗓️  Date : {match_date} | Saison : {season}")
        print(f"⏱️ Date utilisée pour filtre SQL : {match_date} ({type(match_date)})")
        print(f"🏠 Home ID : {home_team_id} | 🛫 Away ID : {away_team_id}")

        # 2. Liste des matchs utilisés pour le cumul
        cursor.execute("""
            SELECT f.id, f.date, home.name AS home_team, away.name AS away_team
            FROM fixtures f
            JOIN teams home ON f.home_team_id = home.id
            JOIN teams away ON f.away_team_id = away.id
            WHERE datetime(f.date) < datetime(?)
              AND f.league_id = ?
              AND f.season = ?
              AND (f.home_team_id = ? OR f.away_team_id = ?)
            ORDER BY f.date
        """, (match_date, league_id, season, home_team_id, away_team_id))
        matches_used = cursor.fetchall()

        print("📅 Matchs utilisés pour cumul :")
        for m in matches_used:
            print(f" - {m[0]} | {m[1][:10]} : {m[2]} vs {m[3]}")

        # 3. Stats cumulées des joueurs
        cursor.execute("""
            SELECT
                p.id, p.name, p.position, ps.team_id,
                COUNT(DISTINCT ps.fixture_id) AS appearances,
                SUM(COALESCE(ps.goals, 0)),
                SUM(COALESCE(ps.assists, 0)),
                SUM(COALESCE(ps.minutes, 0)),
                SUM(COALESCE(ps.shots_total, 0)),
                SUM(COALESCE(ps.shots_on_target, 0)),
                SUM(COALESCE(ps.yellow_cards, 0)),
                SUM(COALESCE(ps.red_cards, 0)),
                SUM(COALESCE(ps.penalty_scored, 0))
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            JOIN fixtures f ON ps.fixture_id = f.id
            WHERE datetime(f.date) < datetime(?)
              AND f.season = ?
              AND (ps.team_id = ? OR ps.team_id = ?)
            GROUP BY ps.player_id
        """, (match_date, season, home_team_id, away_team_id))

        stats = cursor.fetchall()

        for row in stats:
            player = {
                "id": row[0],
                "name": row[1],
                "position": row[2],
                "position_abbr": get_position_abbr(row[2]),
                "team_id": row[3],
                "appearances": row[4],
                "goals": row[5],
                "assists": row[6],
                "minutes": row[7],
                "shots_total": row[8],
                "shots_on_target": row[9],
                "yellow_cards": row[10],
                "red_cards": row[11],
                "penalty_scored": row[12],
                "goals_per_game": round((row[5] or 0) / row[4], 2) if row[4] else 0,
                "assists_per_game": round((row[6] or 0) / row[4], 2) if row[4] else 0,
                "minutes_per_game": round((row[7] or 0) / row[4], 1) if row[4] else 0,
            }

            cursor.execute("SELECT logo FROM teams WHERE id = ?", (player["team_id"],))
            result = cursor.fetchone()
            player["team_logo"] = result[0] if result else None

            if player["team_id"] == home_team_id:
                match_data["home_players"].append(player)
            else:
                match_data["away_players"].append(player)

        print(f"✅ Joueurs domicile : {len(match_data['home_players'])}")
        print(f"✅ Joueurs extérieur : {len(match_data['away_players'])}")
        return match_data


def get_team_id_by_name(conn, team_name):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM teams WHERE name = ?", (team_name,))
    result = cursor.fetchone()
    return result[0] if result else None


def get_player_match_stats(player_id, stat="goals", limit=10, filter_type=None, league_id=None, cut=1, fixture_id=None, season=None):
    print(f"\n🔍 [DEBUG] Appel de get_player_match_stats | player_id: {player_id} | stat: {stat} | filter_type: {filter_type} | league_id: {league_id} | cut: {cut} | season: {season}")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 🔠 Bloc spécial : goals avec filtre avancé (MT, 2MT, intervalles)
        if stat == "goals" and filter_type in (
            "first_half", "second_half", "both_halves",
            "0-15", "15-30", "30-45", "45-60", "60-75", "75-90"
        ):
            base_query = """
                SELECT DISTINCT f.id, DATE(f.date), f.home_goals, f.away_goals
                FROM fixtures f
                JOIN player_stats ps ON ps.fixture_id = f.id
                WHERE ps.player_id = ?
            """
            params = [player_id]
            if league_id:
                base_query += " AND f.league_id = ?"
                params.append(league_id)
            if season:
                base_query += " AND f.season = ?"
                params.append(season)
            base_query += " ORDER BY f.date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(base_query, params)
            recent_matches = cursor.fetchall()
            results = []

            for fixture_id, date, home_goals, away_goals in recent_matches:
                cursor.execute("""
                    SELECT e.elapsed, e.extra
                    FROM fixture_events e
                    WHERE e.fixture_id = ? AND e.player_id = ? AND e.type = 'Goal'
                """, (fixture_id, player_id))
                goals = cursor.fetchall()

                first_half_goals = [e for e in goals if e[0] is not None and (e[0] < 45 or (e[0] == 45 and (e[1] or 0) <= 7))]

                cursor.execute("SELECT minutes FROM player_stats WHERE player_id = ? AND fixture_id = ?", (player_id, fixture_id))
                minutes_row = cursor.fetchone()
                minutes_played = int(minutes_row[0]) if minutes_row and minutes_row[0] is not None else 0

                if filter_type == "first_half":
                    has_goal_but_not_first_half = len(goals) > 0 and len(first_half_goals) == 0
                    if len(first_half_goals) >= cut:
                        minute = int(first_half_goals[0][0] or 0) + int(first_half_goals[0][1] or 0)
                        value = len(first_half_goals)
                    else:
                        value = 1 if has_goal_but_not_first_half else 0.1
                        minute = None
                    results.append({
                        "fixture_id": fixture_id,
                        "date": date,
                        "value": value,
                        "minute": minute,
                        "minutes": minutes_played,
                        "score": f"{home_goals}-{away_goals}",
                        "status": "mt" if value >= cut else "none",
                        "has_goal_but_not_first_half": has_goal_but_not_first_half
                    })

                elif filter_type == "second_half":
                    filtered = [e for e in goals if e[0] is not None and (e[0] > 45 or (e[0] == 45 and (e[1] or 0) > 7))]
                    value = len(filtered) if filtered else 0.1
                    results.append({
                        "fixture_id": fixture_id,
                        "date": date,
                        "value": value,
                        "minute": None,
                        "minutes": minutes_played,
                        "score": f"{home_goals}-{away_goals}",
                        "has_goal_but_not_first_half": False
                    })

                elif filter_type == "both_halves":
                    has_first = len(first_half_goals) > 0
                    has_second = any(e[0] is not None and (e[0] > 45 or (e[0] == 45 and (e[1] or 0) > 7)) for e in goals)
                    if has_first and has_second:
                        value = len(goals)
                        minute = int(goals[0][0] or 0) + int(goals[0][1] or 0)
                    else:
                        value = 1 if len(goals) == 1 else 0.1
                        minute = None
                    results.append({
                        "fixture_id": fixture_id,
                        "date": date,
                        "value": value,
                        "minute": minute,
                        "minutes": minutes_played,
                        "score": f"{home_goals}-{away_goals}",
                        "status": "2mt" if value > 1 else "none",
                        "has_goal_but_not_first_half": len(goals) == 1
                    })

                elif "-" in filter_type:
                    try:
                        min_range, max_range = map(int, filter_type.split("-"))
                        filtered = [e for e in goals if e[0] is not None and min_range <= e[0] < max_range]
                        value = len(filtered) if filtered else 0.1
                        results.append({
                            "fixture_id": fixture_id,
                            "date": date,
                            "value": value,
                            "minute": None,
                            "minutes": minutes_played,
                            "score": f"{home_goals}-{away_goals}",
                            "has_goal_but_not_first_half": False
                        })
                    except Exception as e:
                        print(f"⚠️ Erreur parsing intervalle {filter_type} :", e)

            return results

        # 🌟 DÉCISIF = but ou passe
        elif filter_type == "decisive":
            base_query = """
                SELECT f.id, DATE(f.date), f.home_goals, f.away_goals, ps.goals, ps.assists, ps.minutes
                FROM fixtures f
                JOIN player_stats ps ON ps.fixture_id = f.id
                WHERE ps.player_id = ?
            """
            params = [player_id]
            if league_id:
                base_query += " AND f.league_id = ?"
                params.append(league_id)
            if season:
                base_query += " AND f.season = ?"
                params.append(season)
            base_query += " ORDER BY f.date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(base_query, params)
            rows = cursor.fetchall()
            results = []

            for fixture_id, date, home_goals, away_goals, goals, assists, minutes_played in rows:
                stat_total = (goals or 0) + (assists or 0)
                value = stat_total if stat_total > 0 else 0.1
                results.append({
                    "fixture_id": fixture_id,
                    "date": date,
                    "value": value,
                    "minute": None,
                    "minutes": minutes_played or 0,
                    "score": f"{home_goals}-{away_goals}",
                    "status": "none" if value == 0.1 else None,
                    "has_goal_but_not_first_half": False
                })

            return results

        # 🌟 H2H = matchs contre l'adversaire du jour (multi-saisons)
        elif filter_type == "h2h_only":
            if not fixture_id:
                print("❌ fixture_id requis pour le mode h2h_only")
                return []

            cursor.execute("SELECT home_team_id, away_team_id FROM fixtures WHERE id = ?", (fixture_id,))
            row = cursor.fetchone()
            if not row:
                return []
            home_team_id, away_team_id = row

            cursor.execute("SELECT team_id FROM player_stats WHERE player_id = ? AND fixture_id = ?", (player_id, fixture_id))
            row = cursor.fetchone()
            if not row:
                return []
            player_team_id = row[0]
            opponent_team_id = away_team_id if player_team_id == home_team_id else home_team_id

            query = f"""
                SELECT f.id, DATE(f.date), f.home_goals, f.away_goals, ps.{stat}, ps.minutes
                FROM fixtures f
                JOIN player_stats ps ON ps.fixture_id = f.id
                WHERE ps.player_id = ? AND (f.home_team_id = ? OR f.away_team_id = ?)
                ORDER BY f.date DESC LIMIT ?
            """
            cursor.execute(query, (player_id, opponent_team_id, opponent_team_id, limit))
            rows = cursor.fetchall()
            results = []

            for fixture_id, date, home_goals, away_goals, stat_value, minutes_played in rows:
                value = stat_value if stat_value and stat_value > 0 else 0.1
                results.append({
                    "fixture_id": fixture_id,
                    "date": date,
                    "value": value,
                    "minute": None,
                    "minutes": minutes_played or 0,
                    "score": f"{home_goals}-{away_goals}",
                    "status": "none" if value == 0.1 else None,
                    "has_goal_but_not_first_half": False
                })

            return results

        # 🔁 Fallback par défaut (X1 / X2 / autres stats)
        else:
            base_query = f"""
                SELECT DISTINCT f.id, DATE(f.date), f.home_goals, f.away_goals
                FROM fixtures f
                JOIN player_stats ps ON ps.fixture_id = f.id
                WHERE ps.player_id = ?
            """
            params = [player_id]
            if league_id:
                base_query += " AND f.league_id = ?"
                params.append(league_id)
            if season:
                base_query += " AND f.season = ?"
                params.append(season)
            if filter_type == "home":
                base_query += " AND f.home_team_id = ps.team_id"
            elif filter_type == "away":
                base_query += " AND f.away_team_id = ps.team_id"
            base_query += " ORDER BY f.date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(base_query, params)
            recent_matches = cursor.fetchall()
            results = []

            for fixture_id, date, home_goals, away_goals in recent_matches:
                cursor.execute(f"SELECT {stat}, minutes FROM player_stats WHERE player_id = ? AND fixture_id = ?", (player_id, fixture_id))
                stat_row = cursor.fetchone()
                stat_value = stat_row[0] if stat_row and stat_row[0] is not None else 0
                minutes_played = stat_row[1] if stat_row and stat_row[1] is not None else 0

                if stat == "goals" and (filter_type is None or filter_type == ""):
                    value = stat_value if stat_value >= 2 else (1 if stat_value == 1 else 0.1)
                    has_goal_but_not_first_half = stat_value == 1
                elif stat == "goals" and filter_type == "goals":
                    value = stat_value if stat_value > 0 else 0.1
                    has_goal_but_not_first_half = False
                else:
                    value = stat_value if stat_value > 0 else 0.1
                    has_goal_but_not_first_half = False

                results.append({
                    "fixture_id": fixture_id,
                    "date": date,
                    "value": value,
                    "minute": None,
                    "minutes": minutes_played,
                    "score": f"{home_goals}-{away_goals}",
                    "status": "none" if value == 0.1 else None,
                    "has_goal_but_not_first_half": has_goal_but_not_first_half
                })

            return results












def get_player_name(player_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM players WHERE id = ?", (player_id,))
        result = cursor.fetchone()
        return result[0] if result else None

def get_all_fixtures_grouped_by_country_league(selected_date=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        query = """
            SELECT f.id, f.date, f.league_id, l.name, l.country, l.logo, l.flag,
                   t1.name, t2.name, f.home_goals, f.away_goals
            FROM fixtures f
            JOIN leagues l ON f.league_id = l.id
            JOIN teams t1 ON f.home_team_id = t1.id
            JOIN teams t2 ON f.away_team_id = t2.id
        """
        params = []

        if selected_date:
            query += " WHERE DATE(f.date) = ?"
            params.append(selected_date)

        query += " ORDER BY l.country, l.name, f.date"

        cursor.execute(query, params)
        rows = cursor.fetchall()

    matches_by_country_league = {}
    for row in rows:
        fixture = {
            "id": row[0],
            "date": row[1][:10],
            "league_id": row[2],
            "league_name": row[3],
            "country": row[4],
            "league_logo": row[5],
            "country_flag": row[6],
            "home_team": row[7],
            "away_team": row[8],
            "score": f"{row[9]} - {row[10]}"
        }

        country = fixture["country"]
        league = fixture["league_name"]
        matches_by_country_league.setdefault(country, {}).setdefault(league, []).append(fixture)

    return matches_by_country_league

from data_pipeline.api_utils.utils_api import get_api_json

def get_team_season_stats(team_id, league_id, season):
    response = get_api_json("players", params={
        "team": team_id,
        "league": league_id,
        "season": season
    })

    results = []
    for item in response.get("response", []):
        player = item["player"]
        stats = item["statistics"][0] if item["statistics"] else {}

        results.append({
            "id": player["id"],
            "name": player["name"],
            "position": player.get("position", "?"),
            "position_abbr": get_position_abbr(player.get("position", "?")),
            "team_logo": stats.get("team", {}).get("logo", ""),
            "minutes": stats.get("games", {}).get("minutes", 0),
            "goals": stats.get("goals", {}).get("total", 0),
            "assists": stats.get("goals", {}).get("assists", 0),
            "shots_total": stats.get("shots", {}).get("total", 0),
            "shots_on_target": stats.get("shots", {}).get("on", 0),
            "xg": stats.get("expected", {}).get("goals", 0),
            "xa": stats.get("expected", {}).get("assists", 0)
        })

    return results

def get_player_team_id(fixture_id, player_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Étape 1 : Chercher dans player_stats
        cursor.execute("""
            SELECT team_id FROM player_stats
            WHERE player_id = ? AND fixture_id = ?
        """, (player_id, fixture_id))
        result = cursor.fetchone()
        if result:
            print(f"🔍 team_id trouvé via player_stats : {result[0]}")
            return result[0]
        else:
            print(f"❌ Aucun team_id trouvé dans player_stats pour player {player_id} / fixture {fixture_id}")

        # Étape 2 : Chercher dans player_match_presence
        cursor.execute("""
            SELECT team_id FROM player_match_presence
            WHERE player_id = ? AND fixture_id = ?
        """, (player_id, fixture_id))
        result = cursor.fetchone()
        if result:
            print(f"🔍 team_id trouvé via player_match_presence : {result[0]}")
            return result[0]
        else:
            print(f"❌ Aucun team_id trouvé dans player_match_presence pour player {player_id} / fixture {fixture_id}")

        # Étape 3 : Fallback depuis players
        cursor.execute("""
            SELECT team_id FROM players
            WHERE id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (player_id,))
        result = cursor.fetchone()
        if result:
            print(f"🔁 team_id fallback depuis players : {result[0]}")
            return result[0]
        else:
            print(f"❌ Aucun team_id trouvé dans la table players pour player {player_id}")

    print(f"🛑 Aucun team_id trouvé pour player {player_id} / fixture {fixture_id}")
    return None



def get_match_with_player_stats(fixture_id, player_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # 1. Infos du match
        cursor.execute("""
            SELECT f.id, f.league_id, f.date, f.home_team_id, f.away_team_id,
                   t1.name, t2.name, f.home_goals, f.away_goals
            FROM fixtures f
            JOIN teams t1 ON f.home_team_id = t1.id
            JOIN teams t2 ON f.away_team_id = t2.id
            WHERE f.id = ?
        """, (fixture_id,))
        match = cursor.fetchone()
        if not match:
            print("❌ Match introuvable pour fixture_id :", fixture_id)
            return None

        match_data = {
            "id": match[0],
            "league_id": match[1],
            "date": match[2][:10],
            "home_team_id": match[3],
            "away_team_id": match[4],
            "home_team": match[5],
            "away_team": match[6],
            "home_players": [],
            "away_players": [],
            "home_goals": match[7],
            "away_goals": match[8],
            "players": [],
            "player_team_id": None  # 🔍 Ajout du champ ici
        }

        print(f"📊 Traitement du match : {match_data['home_team']} vs {match_data['away_team']} (ID {fixture_id})")

        # 2. Événements
        cursor.execute("""
            SELECT player_id, assist_id, type, detail
            FROM fixture_events
            WHERE fixture_id = ?
        """, (fixture_id,))
        events = cursor.fetchall()
        print(f"📌 Événements récupérés : {len(events)}")

        # 3. Stats des joueurs
        cursor.execute("""
            SELECT p.id, p.name, p.position, ps.minutes, ps.team_id
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            WHERE ps.fixture_id = ?
        """, (fixture_id,))
        stats = cursor.fetchall()
        print(f"👥 Joueurs avec stats récupérés : {len(stats)}")

        if not stats:
            print("⚠️ Aucun joueur avec stats — retour données de base")
            return match_data

        for row in stats:
            player_id_row = row[0]
            player = {
                "id": player_id_row,
                "name": row[1],
                "position": row[2],
                "position_abbr": get_position_abbr(row[2]),
                "minutes": row[3],
                "team_id": row[4],
                "goals": 0,
                "assists": 0,
                "penalty_scored": 0,
                "yellow_cards": 0,
                "red_cards": 0
            }

            # ➕ Si c’est le joueur demandé, on stocke son équipe
            if player_id and player_id_row == player_id:
                match_data["player_team_id"] = row[4]

            for e_player_id, e_assist_id, e_type, e_detail in events:
                if e_type == "Goal":
                    if e_player_id == player_id_row:
                        player["goals"] += 1
                        if e_detail == "Penalty":
                            player["penalty_scored"] += 1
                    if e_assist_id == player_id_row:
                        player["assists"] += 1

                if e_type == "Card" and e_player_id == player_id_row:
                    if e_detail == "Yellow Card":
                        player["yellow_cards"] += 1
                    elif e_detail == "Red Card":
                        player["red_cards"] += 1

            match_data["players"].append(player)

            if player["team_id"] == match_data["home_team_id"]:
                match_data["home_players"].append(player)
            else:
                match_data["away_players"].append(player)

        print(f"✅ Joueurs domicile : {len(match_data['home_players'])}")
        print(f"✅ Joueurs extérieur : {len(match_data['away_players'])}")
        print(f"🏷️ player_team_id extrait : {match_data['player_team_id']}")

        # 🔄 Fallback si player_team_id est toujours None
        if player_id and not match_data["player_team_id"]:
            print("🔍 Fallback via player_match_presence pour player_id =", player_id)
            cursor.execute("""
                SELECT team_id FROM player_match_presence
                WHERE player_id = ? AND fixture_id = ?
            """, (player_id, fixture_id))
            row = cursor.fetchone()
            if row:
                match_data["player_team_id"] = row[0]
                print(f"✅ team_id trouvé via player_match_presence : {match_data['player_team_id']}")
            else:
                print(f"❌ Aucun team_id trouvé pour player_id={player_id} dans match {fixture_id}")
        
        
                return match_data

    
def repair_player_stats_from_events(fixture_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        print(f"🔍 Recalcul stats joueurs pour match {fixture_id} via events")

        # 1. Vider les champs goals/assists avant recalcul
        cursor.execute("""
            UPDATE player_stats
            SET goals = 0, assists = 0
            WHERE fixture_id = ?
        """, (fixture_id,))

        # 2. Buts : type = 'Goal', detail != 'Own Goal'
        cursor.execute("""
            SELECT player_id, COUNT(*) FROM fixture_events
            WHERE fixture_id = ?
              AND type = 'Goal'
              AND detail != 'Own Goal'
              AND player_id IS NOT NULL
            GROUP BY player_id
        """, (fixture_id,))
        for player_id, goal_count in cursor.fetchall():
            cursor.execute("""
                UPDATE player_stats
                SET goals = ?
                WHERE fixture_id = ? AND player_id = ?
            """, (goal_count, fixture_id, player_id))

        # 3. Passes décisives
        cursor.execute("""
            SELECT assist_id, COUNT(*) FROM fixture_events
            WHERE fixture_id = ?
              AND type = 'Goal'
              AND detail != 'Own Goal'
              AND assist_id IS NOT NULL
            GROUP BY assist_id
        """, (fixture_id,))
        for assist_id, assist_count in cursor.fetchall():
            cursor.execute("""
                UPDATE player_stats
                SET assists = ?
                WHERE fixture_id = ? AND player_id = ?
            """, (assist_count, fixture_id, assist_id))

        conn.commit()
        print(f"✅ Stats corrigées via events pour match {fixture_id}")

def fallback_player_stats_from_events(fixture_id):
    DB_PATH = get_db_path()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"🔧 Fallback : reconstruction des stats via événements pour match {fixture_id}")

    # ❌ Supprime les stats existantes du match
    cursor.execute("DELETE FROM player_stats WHERE fixture_id = ?", (fixture_id,))

    # Ὄc Infos du match pour la saison
    cursor.execute("SELECT date, league_id FROM fixtures WHERE id = ?", (fixture_id,))
    match = cursor.fetchone()
    if not match:
        print(f"⛔ Match {fixture_id} introuvable.")
        return
    match_date, league_id = match
    season = get_season_from_date(match_date, league_id)

    # 📊 Tous les événements du match
    cursor.execute("""
        SELECT player_id, assist_id, type, detail, minute
        FROM fixture_events
        WHERE fixture_id = ?
    """, (fixture_id,))
    events = cursor.fetchall()

    player_stats = {}

    for e in events:
        player_id, assist_id, e_type, detail, minute = e
        if not player_id:
            continue

        if player_id not in player_stats:
            player_stats[player_id] = {
                "goals": 0,
                "assists": 0,
                "yellow": 0,
                "red": 0,
                "in_min": 0,
                "out_min": 90,
                "active": False
            }

        stats = player_stats[player_id]

        # ⚽ Buts
        if e_type == "Goal" and player_id != assist_id:
            stats["goals"] += 1
            stats["active"] = True
        # 🎫 Passes décisives
        if assist_id and assist_id != player_id:
            player_stats.setdefault(assist_id, {
                "goals": 0, "assists": 0, "yellow": 0, "red": 0, "in_min": 0, "out_min": 90, "active": False
            })
            player_stats[assist_id]["assists"] += 1
            player_stats[assist_id]["active"] = True

        # 💛 Carton jaune
        if e_type == "Card" and detail == "Yellow Card":
            stats["yellow"] += 1
            stats["active"] = True

        # 💔 Carton rouge
        if e_type == "Card" and detail == "Red Card":
            stats["red"] += 1
            stats["active"] = True

        # ↺ Substitutions (entrée/sortie)
        if e_type == "subst":
            if detail and "Substitution" in detail:
                if assist_id == player_id:
                    stats["out_min"] = minute
                else:
                    stats["in_min"] = minute

    # ✅ Insère dans player_stats
    for player_id, s in player_stats.items():
        est_min = s["out_min"] - s["in_min"] if s["out_min"] and s["in_min"] is not None else (90 if s["active"] else 0)
        cursor.execute("""
            INSERT INTO player_stats (
                player_id, fixture_id, team_id, minutes, goals, assists,
                yellow_cards, red_cards, season
            )
            SELECT ?, ?, team_id, ?, ?, ?, ?, ?, ?
            FROM fixture_events WHERE fixture_id = ? AND player_id = ? LIMIT 1
        """, (
            player_id, fixture_id, est_min, s["goals"], s["assists"],
            s["yellow"], s["red"], season, fixture_id, player_id
        ))

        # ➕ Crée le joueur s'il n'existe pas
        cursor.execute("SELECT 1 FROM players WHERE id = ?", (player_id,))
        if not cursor.fetchone():
            cursor.execute("INSERT OR IGNORE INTO players (id, name) VALUES (?, ?)", (player_id, "Inconnu"))

    conn.commit()
    conn.close()
    print(f"✅ Fallback terminé pour le match {fixture_id}")

# data_access.py

import sqlite3
from data_pipeline.api_utils.path_utils import get_db_path


def get_team_goal_series_with_rank(team_id, league_id, season):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    # Récupère les derniers matchs où l'équipe a joué et le score est connu
    cursor.execute("""
        SELECT 
            f.date,
            CASE 
                WHEN f.home_team_id = ? THEN f.home_goals
                ELSE f.away_goals
            END as goals
        FROM fixtures f
        WHERE (f.home_team_id = ? OR f.away_team_id = ?)
        AND f.home_goals IS NOT NULL AND f.away_goals IS NOT NULL
        ORDER BY f.date DESC
        LIMIT 20
    """, (team_id, team_id, team_id))
    
    rows = cursor.fetchall()

    # Filtrer la série continue de buts
    streak = []
    for row in rows:
        goals = row[1]
        if goals and goals > 0:
            streak.append({"date": row[0], "goals": goals})
        else:
            break
    streak = list(reversed(streak))

    # Calcul du classement attaque
    cursor.execute("""
        SELECT team_id, SUM(goals) as total_goals
        FROM (
            SELECT home_team_id as team_id, SUM(home_goals) as goals
            FROM fixtures
            WHERE league_id = ? AND season = ? AND home_goals IS NOT NULL
            GROUP BY home_team_id
            UNION ALL
            SELECT away_team_id as team_id, SUM(away_goals) as goals
            FROM fixtures
            WHERE league_id = ? AND season = ? AND away_goals IS NOT NULL
            GROUP BY away_team_id
        )
        GROUP BY team_id
        ORDER BY total_goals DESC
    """, (league_id, season, league_id, season))

    rankings = cursor.fetchall()
    team_rank = next((i + 1 for i, (tid, _) in enumerate(rankings) if tid == team_id), None)
    team_count = len(rankings)

    conn.close()

    return {
        "series": streak,
        "attack_rank": team_rank,
        "team_count": team_count
    }

def get_team_season_stats(team_id, season):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, home_team_id, away_team_id, home_goals, away_goals, home_goals_ht, away_goals_ht
        FROM fixtures
        WHERE (home_team_id = ? OR away_team_id = ?) AND season = ?
        AND home_goals IS NOT NULL AND away_goals IS NOT NULL
    """, (team_id, team_id, season))

    matches = cursor.fetchall()
    total_matches = len(matches)

    goals = 0
    no_goal_matches = 0
    over_1_5 = 0
    over_2_5 = 0
    first_half_goals = 0
    second_half_goals = 0
    matches_with_goal_first_half = 0
    matches_with_goal_second_half = 0
    matches_with_goal = 0

    for match in matches:
        fixture_id, home_id, away_id, home_goals, away_goals, home_goals_ht, away_goals_ht = match

        if team_id == home_id:
            team_goals = home_goals
            team_goals_ht = home_goals_ht
            team_goals_2nd = home_goals - home_goals_ht
        else:
            team_goals = away_goals
            team_goals_ht = away_goals_ht
            team_goals_2nd = away_goals - away_goals_ht

        goals += team_goals

        if team_goals == 0:
            no_goal_matches += 1
        else:
            matches_with_goal += 1

        if team_goals >= 2:
            over_1_5 += 1
        if team_goals >= 3:
            over_2_5 += 1

        first_half_goals += team_goals_ht
        second_half_goals += team_goals_2nd

        if team_goals_ht > 0:
            matches_with_goal_first_half += 1
        if team_goals_2nd > 0:
            matches_with_goal_second_half += 1

    conn.close()

    return {
        "total_matches": total_matches,
        "goals": goals,
        "avg_goals": round(goals / total_matches, 2) if total_matches > 0 else 0,
        "no_goal_matches": no_goal_matches,
        "goal_ratio": round(matches_with_goal / total_matches * 100, 1) if total_matches > 0 else 0,
        "over_1_5_pct": round(over_1_5 / total_matches * 100, 1) if total_matches > 0 else 0,
        "over_2_5_pct": round(over_2_5 / total_matches * 100, 1) if total_matches > 0 else 0,
        "first_half_goals": first_half_goals,
        "second_half_goals": second_half_goals,
        "matches_with_goal_first_half": matches_with_goal_first_half,
        "matches_with_goal_second_half": matches_with_goal_second_half,
    }



def get_current_season_int():
    from datetime import datetime
    today = datetime.today()
    return today.year if today.month >= 7 else today.year - 1

def get_team_goal_ratio(team_id, location="", stat_type="for", league_id=None, season=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if location == "home":
        condition = "f.home_team_id = ?"
        goals_column = "f.home_goals" if stat_type == "for" else "f.away_goals"
        params = [team_id]
    elif location == "away":
        condition = "f.away_team_id = ?"
        goals_column = "f.away_goals" if stat_type == "for" else "f.home_goals"
        params = [team_id]
    else:
        condition = "(f.home_team_id = ? OR f.away_team_id = ?)"
        goals_column = f"""
            CASE 
                WHEN f.home_team_id = ? THEN 
                    {"f.home_goals" if stat_type == "for" else "f.away_goals"}
                ELSE 
                    {"f.away_goals" if stat_type == "for" else "f.home_goals"}
            END
        """
        params = [team_id, team_id, team_id]

    # Ajout du filtre saison + matchs joués
    where_clause = f"""
        WHERE {condition}
        AND f.home_goals IS NOT NULL
        AND f.away_goals IS NOT NULL
    """

    query = f"""
        SELECT COUNT(*) as total_matches,
               SUM(CASE WHEN {goals_column} > 0 THEN 1 ELSE 0 END) as matches_with_goals
        FROM fixtures f
        {where_clause}
    """


    cursor.execute(query, params)
    total_matches, matches_with_goals = cursor.fetchone()
    conn.close()

    

    if not total_matches:
        return 0

    return round((matches_with_goals / total_matches) * 100, 1)

def get_team_avg_goals_per_match(team_id, location="", stat_type="for", league_id=None, season=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if location == "home":
        condition = "f.home_team_id = ?"
        goals_column = "f.home_goals" if stat_type == "for" else "f.away_goals"
        params = [team_id]
    elif location == "away":
        condition = "f.away_team_id = ?"
        goals_column = "f.away_goals" if stat_type == "for" else "f.home_goals"
        params = [team_id]
    else:
        condition = "(f.home_team_id = ? OR f.away_team_id = ?)"
        goals_column = f"""
            CASE 
                WHEN f.home_team_id = ? THEN {"f.home_goals" if stat_type == "for" else "f.away_goals"}
                ELSE {"f.away_goals" if stat_type == "for" else "f.home_goals"}
            END
        """
        params = [team_id, team_id, team_id]

    query = f"""
        SELECT COUNT(*) as total_matches,
               SUM({goals_column}) as total_goals
        FROM fixtures f
        WHERE {condition}
        AND f.home_goals IS NOT NULL AND f.away_goals IS NOT NULL
    """

    cursor.execute(query, params)
    total_matches, total_goals = cursor.fetchone()
    conn.close()

    if not total_matches:
        return 0

    return round(total_goals / total_matches, 2)  # ✅ Moyenne réelle (ex: 2.3)

def insert_empty_stat_if_missing(fixture_id, player_id, team_id, minutes=0, season="2025-2026"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Vérifie si une stat existe déjà pour ce joueur et ce match
    cursor.execute("""
        SELECT COUNT(*) FROM player_stats
        WHERE fixture_id = ? AND player_id = ?
    """, (fixture_id, player_id))
    count = cursor.fetchone()[0]

    if count == 0:
        cursor.execute("""
            INSERT INTO player_stats (
                player_id, fixture_id, team_id, minutes, goals, assists,
                shots_total, shots_on_target, xg, xa,
                penalty_scored, penalty_missed, yellow_cards, red_cards, season
            ) VALUES (?, ?, ?, ?, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ?)
        """, (
            player_id, fixture_id, team_id, minutes, season
        ))
        print(f"✅ Stat vide insérée dans player_stats pour joueur {player_id} (fixture {fixture_id})")

    conn.commit()
    conn.close()

def insert_player_presence(fixture_id, player_id, team_id, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO player_match_presence (
            fixture_id, player_id, team_id, status
        ) VALUES (?, ?, ?, ?)
    """, (fixture_id, player_id, team_id, status))

    conn.commit()
    conn.close()

def get_team_half_time_goal_ratio(team_id, location="", type_="for", season=None):
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"📥 Saison reçue : {season}")

    # 1. On récupère tous les matchs joués avec score MT valide
    query = """
        SELECT id, home_team_id, away_team_id, home_goals_ht, away_goals_ht, home_goals, away_goals
        FROM fixtures
        WHERE season = ?
          AND home_goals_ht IS NOT NULL AND away_goals_ht IS NOT NULL
    """
    params = [season]

    cursor.execute(query, params)
    rows = cursor.fetchall()

    match_count = 0
    one_plus = 0

    print(f"📊 DEBUG - Ratio buts MT ({type_}) | équipe {team_id} | location={location} | saison={season}")
    print("-" * 80)

    for row in rows:
        fixture_id, home_id, away_id, home_ht, away_ht, home_ft, away_ft = row

        # Skip match if not involving the team
        if team_id not in (home_id, away_id):
            continue

        if location == "home" and home_id != team_id:
            continue
        elif location == "away" and away_id != team_id:
            continue

        if type_ == "for":
            if team_id == home_id:
                goals = home_ht
                side = "HOME"
            else:
                goals = away_ht
                side = "AWAY"
        elif type_ == "against":
            if team_id == home_id:
                goals = away_ht
                side = "HOME (contre)"
            else:
                goals = home_ht
                side = "AWAY (contre)"
        else:
            continue  # Si le type est inconnu, on saute

        if goals is not None:
            match_count += 1
            if goals > 0:
                one_plus += 1
            print(f"✔️ Match {fixture_id} → {goals} but(s) {side}")

    conn.close()

    if match_count == 0:
        print(f"⚠️ Aucun match trouvé pour équipe {team_id}")
        return 0

    ratio = round((one_plus / match_count) * 100, 1)
    print("-" * 80)
    print(f"📊 Matchs avec 1+ but en MT : {one_plus} / {match_count}")
    print(f"📈 Pourcentage : {ratio}%")

    return ratio

def get_team_half_time_goal_avg(team_id, location="", type_="for", season=None):
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"\n📊 DEBUG - Moyenne de buts à la mi-temps | équipe {team_id} | location={location} | type={type_} | saison={season}")
    print("-" * 90)

    query = """
        SELECT id, home_team_id, away_team_id, home_goals_ht, away_goals_ht, home_goals, away_goals
        FROM fixtures
        WHERE season = ?
          AND home_goals_ht IS NOT NULL AND away_goals_ht IS NOT NULL
    """
    cursor.execute(query, (season,))
    rows = cursor.fetchall()

    total_goals = 0
    match_count = 0
    one_plus_count = 0

    for row in rows:
        fixture_id, home_id, away_id, home_ht, away_ht, home_ft, away_ft = row

        # Match non concerné
        if team_id not in (home_id, away_id):
            continue

        # DOMICILE
        if home_id == team_id and location in ("", "home"):
            goals = home_ht if type_ == "for" else away_ht
            label = "HOME" if type_ == "for" else "HOME (contre)"
            if goals is not None:
                total_goals += goals
                match_count += 1
                if goals > 0:
                    one_plus_count += 1
                print(f"✔️ Match {fixture_id} → {goals} but(s) {label}")

        # EXTÉRIEUR
        if away_id == team_id and location in ("", "away"):
            goals = away_ht if type_ == "for" else home_ht
            label = "AWAY" if type_ == "for" else "AWAY (contre)"
            if goals is not None:
                total_goals += goals
                match_count += 1
                if goals > 0:
                    one_plus_count += 1
                print(f"✔️ Match {fixture_id} → {goals} but(s) {label}")

    conn.close()

    if match_count == 0:
        print(f"⚠️ Aucun match trouvé pour équipe {team_id}")
        return 0

    avg = total_goals / match_count
    percentage = (one_plus_count / match_count) * 100

    print("-" * 90)
    print(f"📥 Total buts : {total_goals}")
    print(f"📊 Matchs comptabilisés : {match_count}")
    print(f"✅ Matchs avec 1+ but en MT : {one_plus_count} / {match_count}")
    print(f"📈 Moyenne MT : {round(avg, 2)} | Pourcentage 1+ : {round(percentage, 1)}%\n")

    return round(avg, 2)



def get_team_stat_ratio(team_id, stat_type, location="", season=None):
    print(f"📥 Stat demandé : {stat_type} | équipe : {team_id} | location : {location} | saison : {season}")
    season = int(season)  # ✅ Ajout essentiel

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if location == "home":
        team_cond = "home_team_id = ?"
        base_params = [season, team_id]
        where_clause = f"season = ? AND {team_cond}"
    elif location == "away":
        team_cond = "away_team_id = ?"
        base_params = [season, team_id]
        where_clause = f"season = ? AND {team_cond}"
    else:
        team_cond = "(home_team_id = ? OR away_team_id = ?)"
        base_params = [season, team_id, team_id]
        where_clause = f"season = ? AND {team_cond}"

    if stat_type in ["over_1_5", "over_2_5", "over_3_5"]:
        goal_threshold = {"over_1_5": 2, "over_2_5": 3, "over_3_5": 4}[stat_type]
        condition = f"(home_goals + away_goals >= {goal_threshold})"
        params = base_params

    elif stat_type == "btts":
        condition = f"(home_goals > 0 AND away_goals > 0)"
        params = base_params

    elif stat_type == "clean_sheet":
        condition = f"""(
            (home_team_id = ? AND away_goals = 0) OR
            (away_team_id = ? AND home_goals = 0)
        )"""
        params = base_params + [team_id, team_id]

    else:
        print(f"❌ Stat type inconnu : {stat_type}")
        return 0.0

    query_total = f"SELECT COUNT(*) FROM fixtures WHERE {where_clause} AND home_goals IS NOT NULL AND away_goals IS NOT NULL"
    query_stat = f"SELECT COUNT(*) FROM fixtures WHERE {where_clause} AND home_goals IS NOT NULL AND away_goals IS NOT NULL AND {condition}"

    print(f"🔎 Requête totale : {query_total}")
    print(f"🔎 Paramètres total : {base_params}")
    print(f"📊 Requête stat : {query_stat}")
    print(f"📊 Paramètres stat : {params}")

    cursor.execute(query_total, base_params)
    total = cursor.fetchone()[0] or 1
    print(f"📌 Total de matchs trouvés : {total}")

    cursor.execute(query_stat, params)
    count = cursor.fetchone()[0] or 0
    print(f"✅ Matchs correspondant à {stat_type} : {count}")

    ratio = round(100 * count / total, 1)
    conn.close()
    return ratio

def get_match_by_id(fixture_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.id, f.date, f.league_id, f.home_team_id, f.away_team_id,
               f.home_goals, f.away_goals, f.round,
               ht.name as home_team, at.name as away_team,
               ht.logo as home_logo, at.logo as away_logo
        FROM fixtures f
        JOIN teams ht ON f.home_team_id = ht.id
        JOIN teams at ON f.away_team_id = at.id
        WHERE f.id = ?
    """, (fixture_id,))
    row = cursor.fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "date": row[1],
        "league_id": row[2],
        "home_team_id": row[3],
        "away_team_id": row[4],
        "home_goals": row[5],
        "away_goals": row[6],
        "round": row[7],
        "home_team": row[8],
        "away_team": row[9],
        "home_logo": row[10],
        "away_logo": row[11]
    }



def get_upcoming_fixtures_in_league(league_id, exclude_fixture_id, limit=10):
    import re
    from datetime import datetime
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    query = """
        SELECT f.id, f.date, f.round,
               ht.name, ht.logo,
               at.name, at.logo
        FROM fixtures f
        JOIN teams ht ON f.home_team_id = ht.id
        JOIN teams at ON f.away_team_id = at.id
        WHERE f.league_id = ?
          AND f.date > ?
          AND f.id != ?
        ORDER BY f.date ASC
        LIMIT ?
    """
    cursor.execute(query, (league_id, now, exclude_fixture_id, limit))
    rows = cursor.fetchall()

    upcoming = []
    for row in rows:
        match_id, date_str, round_, home_name, home_logo, away_name, away_logo = row

        try:
            date_obj = datetime.fromisoformat(date_str)
            time_str = date_obj.strftime("%H:%M")
        except:
            time_str = ""

        # ✂️ Extraction du numéro de journée uniquement
        matchday = re.search(r'\d+', round_).group() if round_ and re.search(r'\d+', round_) else ""

        home_abbr = get_team_abbr(home_name)
        away_abbr = get_team_abbr(away_name)

        upcoming.append({
            "id": match_id,
            "date": date_str,
            "round": f"J-{matchday}" if matchday else "",
            "time": time_str,
            "home_team": home_name,
            "home_logo": home_logo,
            "home_abbr": home_abbr,
            "away_team": away_name,
            "away_logo": away_logo,
            "away_abbr": away_abbr,
        })

    return upcoming

def get_team_total_goals_avg(team_id, season, location=""):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        query = """
            SELECT f.home_team_id, f.away_team_id, f.home_goals, f.away_goals
            FROM fixtures f
            WHERE (f.home_team_id = ? OR f.away_team_id = ?)
              AND f.season = ?
              AND f.home_goals IS NOT NULL AND f.away_goals IS NOT NULL
        """
        params = [team_id, team_id, season]

        if location == "home":
            query += " AND f.home_team_id = ?"
            params.append(team_id)
        elif location == "away":
            query += " AND f.away_team_id = ?"
            params.append(team_id)

        rows = cursor.execute(query, params).fetchall()

        if not rows:
            return 0.0

        total = 0
        for row in rows:
            _, _, home_goals, away_goals = row
            total += home_goals + away_goals

        return total / len(rows)

def get_goals_distribution_by_interval(team_id, location, season):

    DB_PATH = get_db_path()

    intervals = [
        (0, 15), (16, 30), (31, 45), (46, 60), (61, 75), (76, 90)
    ]
    result = {f"{start}-{end}": {"for": 0, "against": 0} for start, end in intervals}

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        for start, end in intervals:
            # 🔍 Buts marqués par cette équipe
            query_for = """
                SELECT COUNT(*)
                FROM fixture_events e
                JOIN fixtures f ON f.id = e.fixture_id
                WHERE e.type = 'Goal'
                  AND e.team_id = ?
                  AND f.season = ?
                  AND e.elapsed BETWEEN ? AND ?
            """
            params_for = [team_id, season, start, end]

            if location == "home":
                query_for += " AND f.home_team_id = ?"
                params_for.append(team_id)
            elif location == "away":
                query_for += " AND f.away_team_id = ?"
                params_for.append(team_id)

            cursor.execute(query_for, params_for)
            goals_for = cursor.fetchone()[0] or 0

            # 🔍 Buts encaissés contre cette équipe
            query_against = """
                SELECT COUNT(*)
                FROM fixture_events e
                JOIN fixtures f ON f.id = e.fixture_id
                WHERE e.type = 'Goal'
                  AND f.season = ?
                  AND e.elapsed BETWEEN ? AND ?
                  AND (
                        (f.home_team_id = ? AND e.team_id != ?)
                     OR (f.away_team_id = ? AND e.team_id != ?)
                  )
            """
            params_against = [season, start, end, team_id, team_id, team_id, team_id]

            if location == "home":
                query_against += " AND f.home_team_id = ?"
                params_against.append(team_id)
            elif location == "away":
                query_against += " AND f.away_team_id = ?"
                params_against.append(team_id)

            cursor.execute(query_against, params_against)
            goals_against = cursor.fetchone()[0] or 0

            result[f"{start}-{end}"] = {
                "for": goals_for,
                "against": goals_against
            }

    return result
