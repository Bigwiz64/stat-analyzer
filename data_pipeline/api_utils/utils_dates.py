from datetime import datetime

def get_api_season():
    today = datetime.today()
    year = today.year
    return year - 1 if today.month < 7 else year
