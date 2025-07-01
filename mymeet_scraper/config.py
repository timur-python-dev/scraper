import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

BASE_URL = os.getenv("BASE_URL", "https://mymeet.ai")
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "output")
DB_PATH = BASE_DIR / os.getenv("DB_PATH", "scraper_state.db")

MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", 10))

USER_AGENT = os.getenv("USER_AGENT")
HEADERS = {"User-Agent": USER_AGENT} if USER_AGENT else {}
REQUEST_TIMEOUT = 20  

    