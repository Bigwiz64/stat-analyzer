from datetime import datetime

def get_api_season():
    today = datetime.today()
    year = today.year
    return year - 1 if today.month < 7 else year

# utils_dates.py
from datetime import datetime

def get_season_from_date(date_str, league_id):
    date_obj = datetime.strptime(date_str[:10], "%Y-%m-%d")
    year = date_obj.year
    month = date_obj.month

    if league_id in [103, 113, 244, 119]:  # Norvège, Suède, Finlande, Danemark
        return year
    return year if month >= 7 else year - 1
