import os
from dotenv import load_dotenv

load_dotenv()

API_SPORT_KEY = os.getenv("API_SPORT_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "dev")
