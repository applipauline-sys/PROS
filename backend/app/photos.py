"""Accept actual JPEG/PNG images, strip metadata and keep local files only."""

from io import BytesIO
from uuid import uuid4
import warnings
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session
from .database import DATA_DIR
from .models import Photo
from .properties import session

router = APIRouter(prefix="/api/photos")
PHOTO_DIR = DATA_DIR / "photos"
MAX_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 25_000_000


@router.post("", status_code=201)
async def upload_photo(request: Request, db: Session = Depends(session)):
    if request.headers.get("content-type", "").split(";")[0] not in (
        "image/jpeg",
        "image/png",
    ):
        raise HTTPException(415, "Choisissez une photo JPEG ou PNG.")
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > MAX_BYTES:
            raise HTTPException(413, "La photo ne doit pas dépasser 5 Mo.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as original:
                if (
                    original.format not in ("JPEG", "PNG")
                    or original.width * original.height > MAX_PIXELS
                ):
                    raise ValueError("format ou dimensions")
                original.load()
                image = ImageOps.exif_transpose(original).convert("RGB")
                image.thumbnail((2000, 2000))
                output = BytesIO()
                image.save(output, format="JPEG", quality=88)
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise HTTPException(
            422, "Photo illisible ou trop grande (25 millions de pixels maximum)."
        )
    photo_id = str(uuid4())
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    path = PHOTO_DIR / f"{photo_id}.jpg"
    path.write_bytes(output.getvalue())
    try:
        db.add(Photo(id=photo_id, filename=path.name))
        db.commit()
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return {"id": photo_id, "url": f"/api/photos/{photo_id}"}


@router.get("/{photo_id}")
def read_photo(photo_id: str, db: Session = Depends(session)):
    photo = db.get(Photo, photo_id)
    if not photo or not (PHOTO_DIR / photo.filename).is_file():
        raise HTTPException(404, "Photo introuvable.")
    return FileResponse(
        PHOTO_DIR / photo.filename,
        media_type="image/jpeg",
        headers={"X-Content-Type-Options": "nosniff"},
    )
