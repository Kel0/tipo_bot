import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()
load_dotenv(verbose=True)
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

BASE_DIR = Path(__file__).resolve().parent

BOT_API_TOKEN = os.getenv("BOT_API_TOKEN")
DB_LINK = os.getenv("DB_LINK")
