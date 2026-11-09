import os
import subprocess
import sys
from pathlib import Path


def test_migrations_and_health(tmp_path):
    backend = Path(__file__).resolve().parents[1]
    env = {**os.environ, "MORNY_DATA_DIR": str(tmp_path)}
    for _ in range(2):
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=backend,
            env=env,
            check=True,
        )
    subprocess.run(
        [
            sys.executable,
            "-c",
            "from fastapi.testclient import TestClient; from app.main import app; r=TestClient(app).get('/api/health'); assert r.status_code == 200; assert r.json() == {'status':'ok','database':'ok','revision':'0002'}",
        ],
        cwd=backend,
        env=env,
        check=True,
    )
    import sqlite3

    with sqlite3.connect(tmp_path / "morny.sqlite3") as db:
        tables = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    assert set(tables) == {
        ("alembic_version",),
        ("properties",),
        ("photos",),
        ("property_history",),
    }
