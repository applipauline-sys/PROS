from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from .properties import router as property_router
from .photos import router as photo_router
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from .database import engine

app = FastAPI(title="Morny Immobilier", docs_url=None, redoc_url=None)

app.include_router(property_router)
app.include_router(photo_router)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, error: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Vérifiez les champs : valeurs positives, lettres A à G et longueurs autorisées.",
            "fields": [str(e["loc"][-1]) for e in error.errors()],
        },
    )


@app.exception_handler(SQLAlchemyError)
async def database_error(request: Request, error: SQLAlchemyError):
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Enregistrement indisponible. Vos modifications n’ont pas été confirmées. Réessayez après avoir vérifié le serveur local."
        },
    )


@app.get("/api/health")
def health():
    with engine.connect() as connection:
        revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()
    return {"status": "ok", "database": "ok", "revision": revision}


DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.is_dir():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="interface")
