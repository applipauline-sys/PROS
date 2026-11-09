import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("MORNY_DATA_DIR", ROOT / "data")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
engine = create_engine("sqlite:///" + str(DATA_DIR / "morny.sqlite3"), connect_args={"check_same_thread": False})

class Base(DeclarativeBase):
    pass
