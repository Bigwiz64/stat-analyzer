import os
from dotenv import load_dotenv
from data_pipeline.api_utils.utils_api import get_api_json  # ⚠️ Assure-toi que cette fonction existe

load_dotenv()

LEAGUES = [
    (61, "Ligue 1"),
    (62, "Ligue 2"),
    (39, "Premier League"),
    (140, "La Liga"),
    (78, "Bundesliga"),
    (135, "Serie A"),
    (88, "Eredivisie"),
    (94, "Primeira Liga"),
    (203, "Super Lig"),
    (141, "LaLiga2"),
    (179, "Premiership"),
    (4, "A-League"),
    (40, "Championship"),
    (79, "2. Bundesliga"),
]

def check_league_seasons():
    for league_id, league_name in LEAGUES:
        print(f"🔍 {league_name} ({league_id})")
        data = get_api_json("leagues", params={"id": league_id})
        if not data or not data.get("response"):
            print("   ⚠️ Aucune donnée reçue.")
            continue

        seasons = data["response"][0].get("seasons", [])
        years = [str(s["year"]) for s in seasons if "year" in s]
        print("   📅 Saisons disponibles :", ", ".join(years))

if __name__ == "__main__":
    check_league_seasons()
