from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from .database import engine

app = FastAPI(title="Morny Immobilier", docs_url=None, redoc_url=None)

@app.get("/api/health")
def health():
    with engine.connect() as connection:
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    return {"status": "ok", "database": "ok", "revision": revision}

DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="interface")
