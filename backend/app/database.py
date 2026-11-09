import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("MORNY_DATA_DIR", ROOT / "data")).resolve()
DATA_DIR.mkdir(parents=True, exist_ok=True)
engine = create_engine(
    "sqlite:///" + str(DATA_DIR / "morny.sqlite3"),
    connect_args={"check_same_thread": False},
)


class Base(DeclarativeBase):
    pass


@event.listens_for(engine, "connect")
def configure_sqlite(connection, _):
    from .zones import normalize, resolve_city

    connection.create_function("normalize", 1, normalize, deterministic=True)
    connection.create_function(
        "city_zone", 1, lambda city: resolve_city(city)[1], deterministic=True
    )
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=5000")
