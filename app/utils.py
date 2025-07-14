from datetime import datetime
from pytz import timezone, UTC


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

def convert_utc_to_local(utc_datetime_str):
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(utc_datetime_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt.astimezone(timezone("Europe/Paris"))
        except ValueError:
            continue
    return None