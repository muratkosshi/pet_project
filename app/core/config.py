import os

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
JWT_KEY = os.environ.get("JWT_KEY")
REDIS_URL = os.environ.get("REDIS_URL")


BILIMAL_API_URL = "https://api.bilimal.kz/v1/users/auth?source_id=5"
BILIMAL_MAIN_URL = "https://api.bilimal.kz/v1/main?source_id=5"
BILIMAL_PROFILE_URL = "https://api.bilimal.kz/v1/profile/{profile_id}?source_id=5"