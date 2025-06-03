import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from data_pipeline.api_utils.utils_api import get_api_json as call_api

data = call_api("leagues")
for entry in data["response"]:
    country = entry["country"]["name"]
    league_name = entry["league"]["name"]
    league_id = entry["league"]["id"]
    if country.lower() == "norvège" or "norway" in country.lower():
        print(f"{country} - {league_name} (ID: {league_id})")
