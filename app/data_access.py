
import sqlite3
import os
from data_pipeline.api_utils.path_utils import get_db_path


def get_position_abbr(position):
    position_map = {
        "G": "GK", "Goalkeeper": "GK",
        "D": "DF", "Defender": "DF",
        "M": "MF", "Midfielder": "MF",
        "A": "FW", "Attacker": "FW",
        "Left Back": "LB",
        "Right Back": "RB",
        "Center Back": "CB",
        "Centre-Back": "CB",
        "Defensive Midfield": "CDM",
        "Central Midfield": "CM",
        "Attacking Midfield": "CAM",
        "Left Wing": "LW",
        "Right Wing": "RW",
        "Centre-Forward": "ST",
        "Second Striker": "SS"
    }
    return position_map.get(position, position[:2].upper() if position else "?")



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

    # Certaines ligues comme Norvège (103) jouent sur l’année civile
    if league_id == 103:
        return year

    # Pour les autres (saison été → printemps)
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
            return None

        match_date = match[1]
        league_id = match[4]
        season = get_season_for_fixture(match_date, league_id)
        home_team_id = match[2]
        away_team_id = match[3]

        match_data = {
            "id": match[0],
            "date": match[1][:10],
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

        print("📦 Stats cumulées récupérées pour match à venir :", fixture_id)
        print(f"🗓️  Date du match : {match_date}")
        print(f"🏆  League ID : {league_id} | Saison : {season}")
        print(f"🏠  Home team ID : {home_team_id} | 🛫 Away team ID : {away_team_id}")

        # 2. Liste des matchs utilisés pour le cumul
        cursor.execute("""
            SELECT f.id, f.date, home.name AS home_team, away.name AS away_team
            FROM fixtures f
            JOIN teams home ON f.home_team_id = home.id
            JOIN teams away ON f.away_team_id = away.id
            WHERE f.date < ?
              AND f.league_id = ?
              AND f.season = ?
              AND (f.home_team_id = ? OR f.away_team_id = ?)
            ORDER BY f.date
        """, (match_date, league_id, season, home_team_id, away_team_id))
        matches_used = cursor.fetchall()
        print("📅 Matchs utilisés pour le cumul :")
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
                SUM(COALESCE(ps.shots_on_target, 0))
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            JOIN fixtures f ON ps.fixture_id = f.id
            WHERE f.date < ?
              AND f.league_id = ?
              AND f.season = ?
              AND (ps.team_id = ? OR ps.team_id = ?)
            GROUP BY ps.player_id
        """, (match_date, league_id, season, home_team_id, away_team_id))

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

        return match_data





def get_team_id_by_name(conn, team_name):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM teams WHERE name = ?", (team_name,))
    result = cursor.fetchone()
    return result[0] if result else None


def get_player_match_stats(player_id, stat="goals", limit=10, filter_type=None, league_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

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

                cursor.execute("SELECT minutes FROM player_stats WHERE player_id = ? AND fixture_id = ?", (player_id, fixture_id))
                minutes_row = cursor.fetchone()
                minutes_played = int(minutes_row[0]) if minutes_row and minutes_row[0] is not None else 0

                filtered = []

                if filter_type == "first_half":
                    filtered = [e for e in goals if e[0] is not None and (e[0] < 45 or (e[0] == 45 and (e[1] or 0) <= 7))]
                    if filtered:
                        minute = int(filtered[0][0] or 0) + int(filtered[0][1] or 0)
                        results.append({
                            "fixture_id": fixture_id,
                            "date": date,
                            "value": len(filtered),
                            "minute": minute,
                            "minutes": minutes_played,
                            "score": f"{home_goals}-{away_goals}",
                            "status": "mt"
                        })
                    elif goals:
                        minute = int(goals[0][0] or 0) + int(goals[0][1] or 0)
                        results.append({
                            "fixture_id": fixture_id,
                            "date": date,
                            "value": len(goals),
                            "minute": minute,
                            "minutes": minutes_played,
                            "score": f"{home_goals}-{away_goals}",
                            "status": "2mt"
                        })
                    else:
                        results.append({
                            "fixture_id": fixture_id,
                            "date": date,
                            "value": 0.1,
                            "minute": None,
                            "minutes": minutes_played,
                            "score": f"{home_goals}-{away_goals}",
                            "status": "none"
                        })
                    continue

                elif filter_type == "second_half":
                    filtered = [e for e in goals if e[0] is not None and (e[0] > 45 or (e[0] == 45 and (e[1] or 0) > 7))]

                elif filter_type == "both_halves":
                    has_first = any(e[0] is not None and (e[0] < 45 or (e[0] == 45 and (e[1] or 0) <= 7)) for e in goals)
                    has_second = any(e[0] is not None and (e[0] > 45 or (e[0] == 45 and (e[1] or 0) > 7)) for e in goals)
                    value = 1 if has_first and has_second else 0.1
                    minute = int(goals[0][0] or 0) + int(goals[0][1] or 0) if goals else None
                    status = "none" if value == 0.1 else None
                    result = {
                        "fixture_id": fixture_id,
                        "date": date,
                        "value": value,
                        "minute": minute,
                        "minutes": minutes_played,
                        "score": f"{home_goals}-{away_goals}"
                    }
                    if status:
                        result["status"] = status
                    results.append(result)
                    continue

                elif "-" in filter_type:
                    try:
                        min_range, max_range = map(int, filter_type.split("-"))
                        filtered = [e for e in goals if e[0] is not None and min_range <= e[0] < max_range]
                    except Exception as e:
                        print(f"⚠️ Erreur parsing intervalle {filter_type} :", e)

                    if filtered:
                        try:
                            minute = int(filtered[0][0] or 0) + int(filtered[0][1] or 0)
                        except Exception as e:
                            print("⛔ Erreur de calcul de minute:", e)
                            minute = 0
                        results.append({
                            "fixture_id": fixture_id,
                            "date": date,
                            "value": len(filtered),
                            "minute": minute,
                            "minutes": minutes_played,
                            "score": f"{home_goals}-{away_goals}"
                        })
                    else:
                        results.append({
                            "fixture_id": fixture_id,
                            "date": date,
                            "value": 0.1,
                            "minute": None,
                            "minutes": minutes_played,
                            "score": f"{home_goals}-{away_goals}",
                            "status": "none"
                        })
                    continue

                if filtered:
                    minute = int(filtered[0][0] or 0) + int(filtered[0][1] or 0)
                    results.append({
                        "fixture_id": fixture_id,
                        "date": date,
                        "value": len(filtered),
                        "minute": minute,
                        "minutes": minutes_played,
                        "score": f"{home_goals}-{away_goals}"
                    })
                elif goals:
                    minute = int(goals[0][0] or 0) + int(goals[0][1] or 0)
                    results.append({
                        "fixture_id": fixture_id,
                        "date": date,
                        "value": len(goals),
                        "minute": minute,
                        "minutes": minutes_played,
                        "score": f"{home_goals}-{away_goals}"
                    })
                else:
                    results.append({
                        "fixture_id": fixture_id,
                        "date": date,
                        "value": 0.1,
                        "minute": None,
                        "minutes": minutes_played,
                        "score": f"{home_goals}-{away_goals}",
                        "status": "none"
                    })

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

            base_query += " ORDER BY f.date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(base_query, params)
            recent_matches = cursor.fetchall()
            results = []

            for fixture_id, date, home_goals, away_goals in recent_matches:
                cursor.execute(f"""
                    SELECT {stat}, minutes
                    FROM player_stats
                    WHERE player_id = ? AND fixture_id = ?
                    LIMIT 1
                """, (player_id, fixture_id))
                stat_row = cursor.fetchone()
                value = stat_row[0] if stat_row and stat_row[0] is not None else 0.1
                minutes_played = stat_row[1] if stat_row and stat_row[1] is not None else 0

                results.append({
                    "fixture_id": fixture_id,
                    "date": date,
                    "value": value,
                    "minute": None,
                    "minutes": minutes_played,
                    "score": f"{home_goals}-{away_goals}",
                    "status": "none" if value == 0.1 else None
                })

        unique_results = {}
        for res in results:
            fid = res['fixture_id']
            if fid not in unique_results:
                unique_results[fid] = res
        return list(unique_results.values())





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

def get_match_with_player_stats(fixture_id):
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
            "players": []
        }

        # 2. Récupère tous les événements du match
        cursor.execute("""
            SELECT player_id, assist_id, type, detail
            FROM fixture_events
            WHERE fixture_id = ?
        """, (fixture_id,))
        events = cursor.fetchall()

        # 3. Récupère tous les joueurs ayant des stats
        cursor.execute("""
            SELECT p.id, p.name, p.position, ps.minutes, ps.team_id
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            WHERE ps.fixture_id = ?
        """, (fixture_id,))
        stats = cursor.fetchall()

        for row in stats:
            player_id = row[0]
            player = {
                "id": player_id,
                "name": row[1],
                "position": row[2],
                "position_abbr": get_position_abbr(row[2]),
                "minutes": row[3],
                "team_id": row[4],
                "goals": 0,
                "assists": 0
            }

            # Comptage précis des buts et passes
            for e in events:
                e_player_id, e_assist_id, e_type, e_detail = e
                if e_type == "Goal":
                    if e_player_id == player_id and e_assist_id != player_id:
                        player["goals"] += 1
                    if e_assist_id == player_id:
                        player["assists"] += 1

            match_data["players"].append(player)

            if player["team_id"] == match_data["home_team_id"]:
                match_data["home_players"].append(player)
            else:
                match_data["away_players"].append(player)

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

