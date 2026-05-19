import os
from pathlib import Path

from dotenv import load_dotenv


project_root = Path(__file__).resolve().parents[1]
env_path = project_root / ".env"

load_dotenv(env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")
