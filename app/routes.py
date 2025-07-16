from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from pytz import timezone, UTC
from .data_access import (
    get_match_with_player_stats,
    get_player_match_stats,
    get_player_name,
    get_position_abbr,
    get_match_with_cumulative_player_stats,
    get_team_goal_series_with_rank,
    get_team_season_stats,
    get_current_season_int,
    get_team_goal_ratio,
    get_team_avg_goals_per_match,
    get_team_half_time_goal_avg,
    get_team_half_time_goal_ratio,
    get_player_team_id,
    get_upcoming_fixtures_in_league
)
from app.utils import convert_utc_to_local
import sqlite3
from datetime import datetime, timedelta
from data_pipeline.api_utils.path_utils import get_db_path

main = Blueprint('main', __name__)
DB_PATH = get_db_path()


@main.route('/')
def index():
    selected_date = request.args.get("date")
    if not selected_date:
        selected_date = datetime.utcnow().strftime("%Y-%m-%d")

    selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d")

    status_filter = request.args.get("status")

    # Abréviations françaises des jours
    french_abbr = {
        "Mon": "LU", "Tue": "MA", "Wed": "ME", "Thu": "JE",
        "Fri": "VE", "Sat": "SA", "Sun": "DI"
    }

    selected_day_abbr = french_abbr.get(selected_date_obj.strftime('%a'), selected_date_obj.strftime('%a')).upper()

    from pytz import timezone

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        query = '''
            SELECT f.id, f.date, f.league_id, l.name, l.country, l.logo, l.flag,
                   t1.name, t2.name, f.home_goals, f.away_goals
            FROM fixtures f
            JOIN leagues l ON f.league_id = l.id
            JOIN teams t1 ON f.home_team_id = t1.id
            JOIN teams t2 ON f.away_team_id = t2.id
        '''

        params = []
        conditions = []

        # Charger les matchs entre -1 et +1 jour UTC
        start_date = (selected_date_obj - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (selected_date_obj + timedelta(days=1)).strftime("%Y-%m-%d")
        conditions.append("DATE(f.date) BETWEEN ? AND ?")
        params.extend([start_date, end_date])

        if status_filter == "played":
            conditions.append("f.home_goals IS NOT NULL AND f.away_goals IS NOT NULL")
        elif status_filter == "upcoming":
            conditions.append("f.home_goals IS NULL AND f.away_goals IS NULL")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY f.date ASC"
        cursor.execute(query, params)
        rows = cursor.fetchall()

    matches_by_country_league = {}
    for row in rows:
        local_dt = convert_utc_to_local(row[1])

        # ✅ Filtrage par jour local Europe/Paris
        if local_dt.date() != selected_date_obj.date():
            continue

        fixture = {
            "id": row[0],
            "date": local_dt,  # datetime local complet (heure incluse)
            "league_id": row[2],
            "league_name": row[3],
            "country": row[4],
            "league_logo": row[5],
            "country_flag": row[6],
            "home_team": row[7],
            "away_team": row[8],
            "home_goals": row[9],
            "away_goals": row[10]
        }

        matches_by_country_league \
            .setdefault(fixture["country"], {}) \
            .setdefault(fixture["league_name"], []) \
            .append(fixture)

    
    # 🔍 Print pour debug : affichage des ligues et nb de matchs
    print("📊 Matchs par pays et ligue chargés :")
    for country, leagues in matches_by_country_league.items():
        for league_name, matches in leagues.items():
            print(f"  - {country} / {league_name} : {len(matches)} match(s)")

    # Génération des 15 jours autour de la date sélectionnée
    days = []
    for i in range(-7, 8):
        day = selected_date_obj + timedelta(days=i)
        weekday_en = day.strftime('%a')
        days.append({
            "label": day.strftime("%d/%m"),
            "date": day.strftime("%Y-%m-%d"),
            "weekday": french_abbr.get(weekday_en, weekday_en).upper(),
            "is_today": day.date() == datetime.today().date(),
            "is_selected": day.strftime("%Y-%m-%d") == selected_date
        })

    return render_template("index.html",
        matches_by_country_league=matches_by_country_league,
        selected_date=selected_date,
        selected_date_obj=selected_date_obj,
        selected_day_abbr=selected_day_abbr,
        status_filter=status_filter,
        days=days,
        timedelta=timedelta
    )




@main.route('/match/<int:fixture_id>/redirect')
def match_redirect(fixture_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT home_goals, away_goals FROM fixtures WHERE id = ?", (fixture_id,))
        result = cursor.fetchone()

        if result and result[0] is not None and result[1] is not None:
            return redirect(url_for('main.match_detail', fixture_id=fixture_id))
        else:
            return redirect(url_for('main.match_preview', fixture_id=fixture_id))

from .api_sport import get_team_squad  # en haut du fichier

@main.route('/match/<int:fixture_id>/preview')
def match_preview(fixture_id):
    import sqlite3
    from datetime import datetime, timezone
    from pytz import timezone as pytz_timezone, UTC
    from app.data_access import (
        get_match_with_player_stats,
        get_match_with_cumulative_player_stats,
        get_upcoming_fixtures_in_league  # ✅ à ajouter dans data_access.py si pas déjà
    )

    # Connexion DB + récupération des données du match
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.date, f.round, t1.logo, t2.logo, f.league_id
            FROM fixtures f
            JOIN teams t1 ON f.home_team_id = t1.id
            JOIN teams t2 ON f.away_team_id = t2.id
            WHERE f.id = ?
        """, (fixture_id,))
        result = cursor.fetchone()

    if not result:
        return render_template("match_preview.html", match=None)

    match_date_str, match_round, home_logo, away_logo, league_id = result

    # 📅 Conversion date UTC → locale Europe/Paris
    match_date = None
    paris_tz = pytz_timezone("Europe/Paris")

    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            match_date = datetime.strptime(match_date_str, fmt)

            if match_date.tzinfo is None:
                match_date = match_date.replace(tzinfo=UTC)

            match_date = match_date.astimezone(paris_tz)
            break
        except (ValueError, TypeError):
            continue

    # ⏳ Choix de la méthode stats selon date
    now = datetime.now(UTC)
    if match_date and match_date > now:
        print("⏳ Match à venir - cumul des stats")
        match = get_match_with_cumulative_player_stats(fixture_id)
    else:
        print("✅ Match terminé - stats du match")
        match = get_match_with_player_stats(fixture_id)

    if not match:
        return render_template("match_preview.html", match=None)

    # ➕ Ajout des infos supplémentaires
    match["round"] = match_round
    match["date_fr"] = match_date.strftime("%d/%m/%Y")
    match["time"] = match_date.strftime("%H:%M")
    match["league_id"] = league_id

    # 🆕 Récupération des matchs à venir dans la même ligue
    upcoming_fixtures = get_upcoming_fixtures_in_league(league_id, fixture_id)

    return render_template(
        "match_preview.html",
        match=match,
        home_logo=home_logo,
        away_logo=away_logo,
        season=match.get("season", 2025),
        upcoming_fixtures=upcoming_fixtures  # ✅ Passé au template
    )



@main.route('/match/<int:fixture_id>')
def match_detail(fixture_id):
    stat = request.args.get("stat", "goals")
    cut = request.args.get("cut", type=int)
    side_filter = request.args.get("side", "overall")
    page = request.args.get("page", default=1, type=int)
    per_page = 10

    match = get_match_with_player_stats(fixture_id)
    if not match:
        return render_template("match_detail.html", match=None, message="⚠️ Match non trouvé.")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT home_team_id, away_team_id FROM fixtures WHERE id = ?", (fixture_id,))
        home_team_id, away_team_id = cursor.fetchone()

        cursor.execute("SELECT logo FROM teams WHERE id = ?", (home_team_id,))
        home_team_logo = cursor.fetchone()[0]
        cursor.execute("SELECT logo FROM teams WHERE id = ?", (away_team_id,))
        away_team_logo = cursor.fetchone()[0]

        cursor.execute("SELECT referee FROM fixtures WHERE id = ?", (fixture_id,))
        referee = (cursor.fetchone() or [None])[0]

        cursor.execute("""
            SELECT e.elapsed, e.extra, p_in.name AS player_in, p_out.name AS player_out,
                   e.type, e.detail, e.comments, e.team_id
            FROM fixture_events e
            LEFT JOIN players p_in ON e.player_id = p_in.id
            LEFT JOIN players p_out ON e.assist_id = p_out.id
            WHERE e.fixture_id = ?
            ORDER BY e.elapsed, e.extra
        """, (fixture_id,))
        raw_events = cursor.fetchall()

        cursor.execute("""
            SELECT p.name, ps.team_id, ps.minutes, ps.goals, ps.assists,
                   ps.shots_total, ps.shots_on_target,
                   ps.penalty_scored, ps.penalty_missed,
                   ps.yellow_cards, ps.red_cards,
                   ps.xg, ps.xa,
                   t.name, t.logo
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            JOIN teams t ON ps.team_id = t.id
            WHERE ps.fixture_id = ?
            ORDER BY ps.minutes DESC
        """, (fixture_id,))
        all_player_stats = cursor.fetchall()

    if side_filter == "home":
        filtered_stats = [row for row in all_player_stats if row[1] == home_team_id]
    elif side_filter == "away":
        filtered_stats = [row for row in all_player_stats if row[1] == away_team_id]
    else:
        filtered_stats = all_player_stats

    total_players = len(filtered_stats)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_stats = filtered_stats[start:end]
    total_pages = (total_players + per_page - 1) // per_page

    events = []
    score_home = score_away = 0
    for e in raw_events:
       elapsed = int(e[0] or 0)  # e[0] = elapsed
       extra = int(e[1] or 0)    # e[1] = extra

       # 🕒 Format affiché (ex : 45+2)
       display_minute = f"{elapsed}+{extra}" if extra > 0 else f"{elapsed}"

       # 🧠 minute_int utilisé pour séparer 1re et 2e MT (ex : tri, regroupement)
       if elapsed < 45:
           minute_int = elapsed  # 1re MT
       elif elapsed == 45 and extra <= 7:
           minute_int = 45       # 1re MT (temps additionnel acceptable)
       else:
           minute_int = elapsed + extra  # 2e MT

       side = "home" if e[7] == home_team_id else "away"
       score_after = ""

       if e[4].lower() == "goal":
           if side == "home":
               score_home += 1
           else:
               score_away += 1
           score_after = f"{score_home}-{score_away}"

       events.append({
           "minute": f"{display_minute}'",
           "minute_int": minute_int,
           "side": side,
           "type": e[4].lower(),
           "detail": e[5] or "",
           "player": e[2] or "?",
           "assist": e[3] or "",
           "player_in": e[2] or "?",
           "player_out": e[3] or "",
           "comments": f"({e[6]})" if e[6] else "",
           "score_after": score_after
       })


    events.sort(key=lambda e: e["minute_int"])
    has_next = end < total_players

    return render_template("match_detail.html",
        match=match,
        stat=stat,
        cut=cut,
        events=events,
        home_logo=home_team_logo,
        away_logo=away_team_logo,
        referee=referee,
        player_stats=paginated_stats,
        side_filter=side_filter,
        page=page,
        total_pages=total_pages,
        has_next=has_next
    )




@main.route('/player/<int:player_id>')
def player_detail(player_id):
    stat = request.args.get("stat", "goals")
    cut = request.args.get("cut", type=int)
    limit = request.args.get("limit", type=int, default=10)
    from_match = request.args.get("from_match", type=int)

    player_name = get_player_name(player_id)
    match_stats = get_player_match_stats(player_id, stat, limit)

    return render_template(
        "player_detail.html",
        player_id=player_id,
        player_name=player_name,
        stats=match_stats,
        stat=stat,
        cut=cut,
        limit=limit,
        from_match=from_match
    )

@main.route('/search')
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return redirect(url_for("main.index"))

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, name FROM players WHERE name LIKE ?", (f"%{query}%",))
        players = cursor.fetchall()

        if len(players) == 1:
            return redirect(url_for("main.player_detail", player_id=players[0][0]))

        cursor.execute("SELECT id, name FROM teams WHERE name LIKE ?", (f"%{query}%",))
        teams = cursor.fetchall()

        if len(players) == 0 and len(teams) == 1:
            team_id = teams[0][0]
            cursor.execute("""
                SELECT id FROM fixtures 
                WHERE home_team_id = ? OR away_team_id = ?
                ORDER BY date DESC
                LIMIT 1
            """, (team_id, team_id))
            match = cursor.fetchone()
            if match:
                return redirect(url_for("main.match_detail", fixture_id=match[0]))

    return render_template("search_results.html", query=query, players=players, teams=teams)

@main.route("/team/<int:team_id>")
def team_matches(team_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT name, logo FROM teams WHERE id = ?", (team_id,))
        team = cursor.fetchone()
        if not team:
            return render_template("team_matches.html", team_name="Inconnue", matches=[], stats={}, logo=None)

        team_name, logo_url = team

        cursor.execute("""
            SELECT f.id, f.date, t1.name, t2.name, f.home_goals, f.away_goals, f.home_team_id, f.away_team_id
            FROM fixtures f
            JOIN teams t1 ON f.home_team_id = t1.id
            JOIN teams t2 ON f.away_team_id = t2.id
            WHERE f.home_team_id = ? OR f.away_team_id = ?
            ORDER BY f.date DESC
        """, (team_id, team_id))
        rows = cursor.fetchall()

        matches = []
        stats = {"joués": 0, "gagnés": 0, "nuls": 0, "perdus": 0, "marqués": 0, "encaissés": 0}

        for row in rows:
            local_date = convert_utc_to_local(row[1])
            fixture = {
                "id": row[0],
                "date": local_date[:10],
                "home_team": row[2],
                "away_team": row[3],
                "score": f"{row[4]} - {row[5]}"
            }
            matches.append(fixture)

            is_home = row[6] == team_id
            goals_for = row[4] if is_home else row[5]
            goals_against = row[5] if is_home else row[4]
            stats["joués"] += 1
            stats["marqués"] += goals_for
            stats["encaissés"] += goals_against
            if goals_for > goals_against:
                stats["gagnés"] += 1
            elif goals_for == goals_against:
                stats["nuls"] += 1
            else:
                stats["perdus"] += 1

    return render_template(
        "team_matches.html",
        team_name=team_name,
        logo=logo_url,
        matches=matches,
        stats=stats,
        classement_attaque=None,
        classement_defense=None
    )

@main.route('/calendar')
def calendar():
    selected_date_str = request.args.get("date")
    
    if selected_date_str:
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d")
    else:
        selected_date = datetime.today()

    dates = []
    for i in range(-7, 8):
        day = selected_date + timedelta(days=i)
        dates.append({
            "label": day.strftime("%d/%m"),
            "date": day.strftime("%Y-%m-%d"),
            "weekday": day.strftime("%a").upper(),
            "is_today": day.date() == datetime.today().date(),
            "is_selected": day.date() == selected_date.date()
        })

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.id, f.date, t1.name, t2.name, f.home_goals, f.away_goals, l.name, l.logo
            FROM fixtures f
            JOIN teams t1 ON f.home_team_id = t1.id
            JOIN teams t2 ON f.away_team_id = t2.id
            JOIN leagues l ON f.league_id = l.id
            WHERE DATE(f.date) = ?
            ORDER BY f.date ASC
        """, (selected_date.strftime("%Y-%m-%d"),))
        rows = cursor.fetchall()

    matches = []
    for row in rows:
        local_date = convert_utc_to_local(row[1])
        matches.append({
            "id": row[0],
            "date": local_date,
            "home_team": row[2],
            "away_team": row[3],
            "home_goals": row[4],
            "away_goals": row[5],
            "league_name": row[6],
            "league_logo": row[7]
        })

    return render_template("calendar.html", matches=matches, dates=dates, selected_date=selected_date.strftime("%Y-%m-%d"))

@main.route('/match/<int:fixture_id>/stats')
def match_stats_api(fixture_id):
    stat = request.args.get("stat", "goals")
    cut = request.args.get("cut", type=int)
    side_filter = request.args.get("side", "all")
    page = request.args.get("page", default=1, type=int)
    per_page = 10

    sort_by = request.args.get("sort_by", "minutes")
    sort_order = request.args.get("sort_order", "desc")

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT home_team_id, away_team_id FROM fixtures WHERE id = ?", (fixture_id,))
        home_team_id, away_team_id = cursor.fetchone()

        base_query = f"""
            SELECT p.name, ps.team_id, ps.minutes, ps.goals, ps.assists,
                   ps.shots_total, ps.shots_on_target,
                   ps.penalty_scored, ps.penalty_missed,
                   ps.yellow_cards, ps.red_cards,
                   ps.xg, ps.xa,
                   t.name, t.logo
            FROM player_stats ps
            JOIN players p ON ps.player_id = p.id
            JOIN teams t ON ps.team_id = t.id
            WHERE ps.fixture_id = ?
        """

        order_clause = f"ORDER BY ps.{sort_by} {sort_order.upper()}"
        cursor.execute(base_query + order_clause, (fixture_id,))
        all_player_stats = cursor.fetchall()

    if side_filter == "home":
        filtered_stats = [row for row in all_player_stats if row[1] == home_team_id]
    elif side_filter == "away":
        filtered_stats = [row for row in all_player_stats if row[1] == away_team_id]
    else:
        filtered_stats = all_player_stats

    total_players = len(filtered_stats)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_stats = filtered_stats[start:end]
    has_next = end < total_players

    players = [{
        "name": row[0],
        "team_id": row[1],
        "minutes": row[2] or 0,
        "goals": row[3] or 0,
        "assists": row[4] or 0,
        "shots_total": row[5] or 0,
        "shots_on_target": row[6] or 0,
        "penalty_scored": row[7] or 0,
        "penalty_missed": row[8] or 0,
        "yellow_cards": row[9] or 0,
        "red_cards": row[10] or 0,
        "xg": round(row[11] or 0, 2),
        "xa": round(row[12] or 0, 2),
        "team_name": row[13],
        "team_logo": row[14],
        "side": "home" if row[1] == home_team_id else "away"
    } for row in paginated_stats]

    return {
        "players": players,
        "has_next": has_next,
        "page": page
    }

@main.route('/player/<int:player_id>/history')
def player_stat_history(player_id):
    from datetime import datetime

    stat = request.args.get("stat", "goals")
    limit = int(request.args.get("limit", 5))
    filter_type = request.args.get("filter", "")
    cut = int(request.args.get("cut", 1))
    fixture_id = request.args.get("fixture_id", type=int)

    try:
        def count_hits(data):
            if filter_type == "first_half":
                return sum(1 for d in data if d.get("status") == "mt")
            elif filter_type == "both_halves":
                return sum(1 for d in data if d.get("value", 0) >= 1 and d.get("status") != "none")
            else:
                return sum(1 for d in data if float(d.get("value", 0)) >= float(cut))

        def format_ratio(data):
            total = len(data)
            hits = count_hits(data)
            if total == 0:
                return "-"
            percent = round((hits / total) * 100)
            return f"{hits}/{total} ({percent}%)"

        def total_goals(data):
            return sum(float(d.get("value", 0)) for d in data if d.get("value", 0) > 0.1)

        match = get_match_with_player_stats(fixture_id, player_id)
        if not match:
            return jsonify({"error": "Fixture introuvable"}), 404
        league_id = match["league_id"]

        # Historique principal
        if filter_type == "home_only":
            history_dynamic = get_player_match_stats(player_id, stat, limit, filter_type="home", league_id=league_id)
        elif filter_type == "away_only":
            history_dynamic = get_player_match_stats(player_id, stat, limit, filter_type="away", league_id=league_id)
        else:
            history_dynamic = get_player_match_stats(player_id, stat, limit, filter_type, league_id=league_id)

        # Marquer les 0 comme 0.1 si joueur a joué
        for item in history_dynamic:
            if item.get("value") == 0 and item.get("minutes", 0) > 0:
                item["value"] = 0.1

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT fixture_id, status FROM player_match_presence WHERE player_id = ?", (player_id,))
            absences = cursor.fetchall()
            absent_ids = [row[0] for row in absences]
            status_map = {row[0]: row[1] for row in absences}

        fixture_ids = list(set(m["fixture_id"] for m in history_dynamic) | set(absent_ids))
        team_info_map, score_map, date_map = {}, {}, {}

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            if fixture_ids:
                placeholders = ",".join("?" for _ in fixture_ids)

                # Home/Away ID
                cursor.execute(f"""
                    SELECT f.id, f.home_team_id, f.away_team_id
                    FROM fixtures f
                    WHERE f.id IN ({placeholders})
                """, fixture_ids)
                for fid, home_id, away_id in cursor.fetchall():
                    team_info_map[fid] = {
                        "home_team_id": home_id,
                        "away_team_id": away_id,
                        "player_team_id": None
                    }

                # Score + noms
                cursor.execute(f"""
                    SELECT f.id, f.date, f.home_goals, f.away_goals, t1.name, t2.name
                    FROM fixtures f
                    JOIN teams t1 ON f.home_team_id = t1.id
                    JOIN teams t2 ON f.away_team_id = t2.id
                    WHERE f.id IN ({placeholders})
                """, fixture_ids)
                for fid, date_str, hg, ag, home_name, away_name in cursor.fetchall():
                    date_map[fid] = date_str
                    score_map[fid] = f"{home_name} {hg} - {ag} {away_name}" if hg is not None and ag is not None else ""

        # 🧲 Récupération du team_id par fallback
        for fid in fixture_ids:
            team_id = get_player_team_id(fid, player_id)
            if fid in team_info_map:
                team_info_map[fid]["player_team_id"] = team_id

        # Ajout des absences à l'historique
        existing_ids = {m["fixture_id"] for m in history_dynamic}
        for fid in absent_ids:
            if fid not in existing_ids:
                history_dynamic.append({
                    "fixture_id": fid,
                    "value": 0,
                    "minutes": 0,
                    "date": date_map.get(fid, ""),
                    "home_team_id": team_info_map.get(fid, {}).get("home_team_id"),
                    "away_team_id": team_info_map.get(fid, {}).get("away_team_id"),
                    "player_team_id": team_info_map.get(fid, {}).get("player_team_id"),
                    "status": status_map.get(fid, "absent"),
                    "score": score_map.get(fid, "")
                })

        # Ajout infos aux lignes
        for match_item in history_dynamic:
            fid = match_item["fixture_id"]
            info = team_info_map.get(fid, {})
            match_item.update({
                "home_team_id": info.get("home_team_id"),
                "away_team_id": info.get("away_team_id"),
                "player_team_id": info.get("player_team_id"),
                "status": status_map.get(fid, match_item.get("status", "")),
                "score": score_map.get(fid, match_item.get("score", "")),
                "date": match_item.get("date") or date_map.get(fid, "")
            })

            try:
                raw_date = match_item.get("date", "")
                if "T" in raw_date:
                    dt = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S%z")
                    match_item["date"] = dt.strftime("%Y-%m-%d")
            except Exception as e:
                print(f"⚠️ Erreur conversion date pour match {fid} : {e}")
                match_item["date"] = ""

        history_dynamic.sort(
            key=lambda m: datetime.strptime(m.get("date", ""), "%Y-%m-%d") if m.get("date") else datetime.min,
            reverse=True
        )

        # 📊 Statistiques
        history_5 = get_player_match_stats(player_id, stat, 5, filter_type, league_id=league_id)
        history_10 = get_player_match_stats(player_id, stat, 10, filter_type, league_id=league_id)
        history_20 = get_player_match_stats(player_id, stat, 20, filter_type, league_id=league_id)
        all_stats = get_player_match_stats(player_id, stat, 1000, filter_type, league_id=league_id)

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ps.fixture_id, f.date, f.home_team_id, f.away_team_id, ps.team_id
                FROM player_stats ps
                JOIN fixtures f ON f.id = ps.fixture_id
                WHERE ps.player_id = ?
                ORDER BY f.date DESC
            """, (player_id,))
            all_matches = cursor.fetchall()

        player_fixture_ids = {m[0] for m in all_matches}

        # 🧠 H2H / Localisation
        player_team_id, match_dict, h2h_opponent_id = None, None, None
        for m in all_matches:
            if int(m[0]) == fixture_id:
                player_team_id = m[4]
                match_dict = {"home_team_id": m[2], "away_team_id": m[3]}
                h2h_opponent_id = m[2] if m[3] == player_team_id else m[3]
                break

        # 🔄 Fallback team_id
        if not player_team_id:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT team_id FROM player_match_presence
                    WHERE player_id = ? AND fixture_id = ?
                """, (player_id, fixture_id))
                result = cursor.fetchone()
                if result:
                    player_team_id = result[0]
                    print(f"🔄 Récupéré depuis player_match_presence : team_id = {player_team_id}")

        if not player_team_id:
            player_team_id = get_player_team_id(fixture_id, player_id)
            print(f"🧲 fallback via get_player_team_id : {player_team_id}")

        if not match_dict and match:
            match_dict = {
                "home_team_id": match.get("home_team_id"),
                "away_team_id": match.get("away_team_id")
            }

        # 🧭 Calcul player_location
        print(f"🧪 DEBUG avant calcul player_location | player_team_id = {player_team_id} | match_dict = {match_dict}")
        player_location = None
        if match_dict and player_team_id:
            if match_dict["home_team_id"] == player_team_id:
                player_location = "home"
            elif match_dict["away_team_id"] == player_team_id:
                player_location = "away"

        print(f"📍 player_location = {player_location}")

        # 📊 Calculs filtres
        h2h_ids = {m[0] for m in all_matches if (m[2] == h2h_opponent_id or m[3] == h2h_opponent_id)}
        h2h_stats = [s for s in all_stats if s["fixture_id"] in h2h_ids]
        home_ids = [m[0] for m in all_matches if m[2] == m[4]]
        away_ids = [m[0] for m in all_matches if m[3] == m[4]]
        home_stats = [s for s in all_stats if s["fixture_id"] in home_ids]
        away_stats = [s for s in all_stats if s["fixture_id"] in away_ids]
        season_played_stats = [s for s in all_stats if s["fixture_id"] in player_fixture_ids]

        return jsonify({
            "history": history_dynamic,
            "performance": {
                "last_5": f"{format_ratio(history_5)} | {total_goals(history_5)} But",
                "last_10": f"{format_ratio(history_10)} | {total_goals(history_10)} But",
                "last_20": f"{format_ratio(history_20)} | {total_goals(history_20)} But",
                "h2h": f"{format_ratio(h2h_stats)} | {total_goals(h2h_stats)} But",
                "home": f"{format_ratio(home_stats)} | {total_goals(home_stats)} But",
                "away": f"{format_ratio(away_stats)} | {total_goals(away_stats)} But",
                "season": f"{format_ratio(season_played_stats)} | {total_goals(season_played_stats)} But"
            },
            "player_location": player_location
        })

    except Exception as e:
        print("❌ ERREUR :", e)
        return jsonify({"error": str(e)}), 500















def get_current_season():
    today = datetime.today()
    year = today.year
    # Si on est avant juillet, on est dans la 2ᵉ partie de la saison précédente
    if today.month < 7:
        return f"{year - 1}-{year}"
    else:
        return f"{year}-{year + 1}"

@main.route('/compare_players')
def compare_players():
    from flask import request, jsonify

    ids = request.args.get("ids", "")
    stat = request.args.get("stat", "goals")
    limit = int(request.args.get("limit", 5))
    filter_type = request.args.get("filter", "")
    fixture_id = request.args.get("fixture_id", type=int)

    try:
        player_ids = [int(pid) for pid in ids.split(",") if pid.isdigit()]
        results = []

        for pid in player_ids:
            match = get_match_with_player_stats(fixture_id)
            league_id = match["league_id"] if match else None

            history = get_player_match_stats(pid, stat, limit, filter_type, league_id=league_id)
            results.append({
                "id": pid,
                "name": get_player_name(pid),  # À adapter selon ta fonction utilitaire
                "history": history
            })

        return jsonify({"players": results})
    except Exception as e:
        print("❌ ERREUR /compare_players:", e)
        return jsonify({"error": str(e)}), 500
    
    # routes.py

@main.route('/team/<int:team_id>/goal_series')
def get_team_goal_series_route(team_id):
    try:
        fixture_id = request.args.get("fixture_id", type=int)
        if not fixture_id:
            return jsonify({"error": "fixture_id requis"}), 400

        # Connexion à la base
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()

        # Récupération de la ligue et saison du match
        cursor.execute("SELECT league_id, season FROM fixtures WHERE id = ?", (fixture_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "Match non trouvé"}), 404

        league_id, season = row

        # Appel à la fonction principale
        data = get_team_goal_series_with_rank(team_id, league_id, season)
        return jsonify(data)

    except Exception as e:
        import traceback
        traceback.print_exc()  # Montre l'erreur dans la console
        return jsonify({"error": str(e)}), 500


@main.route("/team/<int:team_id>/goal_ratio")
def team_goal_ratio(team_id):
    location = request.args.get("location", "")
    stat_type = request.args.get("type", "for")
    league_id = request.args.get("league_id", type=int)
    season = request.args.get("season", type=int)

    ratio = get_team_goal_ratio(team_id, location, stat_type, league_id, season)
    return jsonify({"ratio": ratio})

@main.route("/team/<int:team_id>/goal_avg")
def team_goal_avg(team_id):
    location = request.args.get("location", "")
    stat_type = request.args.get("type", "for")
    league_id = request.args.get("league_id", type=int)
    season = request.args.get("season", type=int)

    ratio = get_team_avg_goals_per_match(team_id, location, stat_type, league_id, season)
    return jsonify({"ratio": ratio})

@main.route('/debug_242')
def debug_242():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.id, f.date, f.home_team_id, f.away_team_id, f.home_goals, f.away_goals
            FROM fixtures f
            WHERE f.league_id = 242
            ORDER BY f.date ASC
        """)
        rows = cursor.fetchall()

    print(f"✅ {len(rows)} matchs trouvés")
    for r in rows:
        print(f"Match {r[0]} : {r[2]} vs {r[3]} | Score: {r[4]} - {r[5]}")

    return f"<h1>{len(rows)} matchs trouvés pour la ligue 242 (sans JOIN)</h1>"

@main.route("/team/<int:team_id>/half_time_goal_ratio")
def half_time_goal_ratio(team_id):
    location = request.args.get("location", "")
    type_ = request.args.get("type", "for")
    season = request.args.get("season")

    if not season:
        print("⚠️ Aucune saison reçue")
    else:
        print(f"📥 Saison reçue : {season}")

    ratio = get_team_half_time_goal_ratio(team_id, location, type_, season)
    return jsonify(ratio=ratio)



@main.route("/team/<int:team_id>/half_time_goal_avg")
def half_time_goal_avg(team_id):
    location = request.args.get("location", "")
    type_ = request.args.get("type", "for")
    season = request.args.get("season")

    avg = get_team_half_time_goal_avg(team_id, location, type_, season)
    return jsonify({"ratio": avg})

@main.route('/team/<int:team_id>/season_stat')
def get_team_season_stat(team_id):
    from flask import request, jsonify
    from app.data_access import get_team_stat_ratio

    stat_type = request.args.get("type")         # ex: "over_2_5"
    location = request.args.get("location", "")  # "", "home", "away"
    season = request.args.get("season")

    if not stat_type or not season:
        return jsonify({"error": "Missing parameters"}), 400

    ratio = get_team_stat_ratio(team_id, stat_type, location, season)
    return jsonify({"ratio": ratio})

@main.route('/team/<int:team_id>/season_stats')
def get_team_season_stats(team_id):
    from flask import request, jsonify
    from app.data_access import get_team_stat_ratio

    season = request.args.get("season")
    location = request.args.get("location", "")  # overall, home, away

    if not season:
        return jsonify({"error": "Missing parameters"}), 400

    stat_types = ["over_1_5", "over_2_5", "over_3_5", "btts", "clean_sheet"]

    result = {}
    for stat in stat_types:
        ratio = get_team_stat_ratio(team_id, stat, location, season)
        result[stat] = ratio

    print(f"📤 Statistiques renvoyées pour l'équipe {team_id} ({location}, saison {season}) : {result}")
    return jsonify(result)

