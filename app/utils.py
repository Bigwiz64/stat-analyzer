from datetime import datetime
from pytz import timezone, UTC

TEAM_ABBREVIATIONS = {
    "Atlanta United FC": "ATL",
    "Austin": "AUS",
    "CF Montreal": "MTL",
    "Charlotte": "CLT",
    "Chicago Fire": "CHI",
    "Colorado Rapids": "COL",
    "Columbus Crew": "CLB",
    "DC United": "DC",
    "FC Cincinnati": "CIN",
    "FC Dallas": "DAL",
    "Houston Dynamo": "HOU",
    "Inter Miami": "MIA",
    "Los Angeles FC": "LAFC",
    "Los Angeles Galaxy": "LA",
    "Minnesota United FC": "MIN",
    "Nashville SC": "NSH",
    "New England Revolution": "NE",
    "New York City FC": "NYC",
    "New York Red Bulls": "RBNY",
    "Orlando City SC": "ORL",
    "Philadelphia Union": "PHI",
    "Portland Timbers": "POR",
    "Real Salt Lake": "RSL",
    "San Diego": "SD",
    "San Jose Earthquakes": "SJ",
    "Seattle Sounders": "SEA",
    "Sporting Kansas City": "SKC",
    "St. Louis City": "STL",
    "Toronto FC": "TOR",
    "Vancouver Whitecaps": "VAN"
}

def get_team_abbr(team_name):
    return TEAM_ABBREVIATIONS.get(team_name, team_name[:3].upper() if team_name else "?")


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