"""Use a completely separate database and photo directory for the entire test run."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

TEST_DATA = tempfile.TemporaryDirectory(prefix="morny-test-")
os.environ["MORNY_DATA_DIR"] = TEST_DATA.name
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, check=True
)


@pytest.fixture
def client():
    # Import the app only after selecting and migrating the isolated test database.
    from app.main import app
    from app.database import engine
    from app.models import Property, PropertyHistory, Photo

    with Session(engine) as db:
        for model in (PropertyHistory, Property, Photo):
            db.execute(delete(model))
        db.commit()
    with TestClient(app) as test_client:
        yield test_client
