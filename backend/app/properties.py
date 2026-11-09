"""Local property API. Transactions preserve each edit and its history together."""

from datetime import timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import asc, case, desc, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError
from .database import engine
from .models import Photo, Property, PropertyHistory, now
from .schemas import PropertyInput, PropertyUpdate, Source, Status
from .zones import CITIES, ZONES, normalize, resolve_city

router = APIRouter(prefix="/api")
ZONE_META = {z["id"]: {k: v for k, v in z.items() if k != "cities"} for z in ZONES}
ZONE_META[0] = {"id": 0, "name": "Hors zone", "color": "#77786f"}
STATUSES = [
    "Non prospecté",
    "Prospection prévue",
    "Prospection impossible",
    "Prospecté",
]


def session():
    with Session(engine) as db:
        yield db


def timestamp(value):
    return value.replace(tzinfo=timezone.utc).isoformat() if value else None


def serialize(item):
    values = {key: getattr(item, key) for key in PropertyInput.model_fields}
    values["next_action"] = item.next_action.isoformat() if item.next_action else None
    values.update(
        id=item.id,
        version=item.version,
        created_at=timestamp(item.created_at),
        updated_at=timestamp(item.updated_at),
        zone=ZONE_META[resolve_city(item.city)[1]],
        photo_url=f"/api/photos/{item.photo_id}" if item.photo_id else None,
    )
    return values


def record(db, item, action):
    try:
        db.flush()
    except StaleDataError:
        db.rollback()
        raise HTTPException(
            409, "Cette fiche a changé. Rechargez-la avant de réessayer."
        )
    db.add(
        PropertyHistory(property_id=item.id, action=action, snapshot=serialize(item))
    )


def commit(db):
    try:
        db.commit()
    except StaleDataError:
        db.rollback()
        raise HTTPException(
            409, "Cette fiche a changé. Rechargez-la avant de réessayer."
        )


def get_item(db, item_id):
    item = db.get(Property, item_id)
    if item is None or item.deleted:
        raise HTTPException(404, "Bien introuvable ou supprimé.")
    return item


def input_values(data, db):
    values = data.model_dump(exclude={"version"})
    values["city"] = resolve_city(values["city"])[0]
    if values["photo_id"] and db.get(Photo, values["photo_id"]) is None:
        raise HTTPException(422, "Photo introuvable. Téléversez-la de nouveau.")
    return values


@router.get("/property-options")
def options():
    return {"cities": CITIES, "zones": [*ZONES, ZONE_META[0]], "statuses": STATUSES}


@router.get("/properties")
def list_properties(
    q: str = Query("", max_length=500),
    city: str = Query("", max_length=150),
    zone: int | None = Query(None, ge=0, le=9),
    source: Source | None = None,
    status: Status | None = None,
    sort: str = Query(
        "created_at", pattern="^(city|zone|created_at|updated_at|next_action|status)$"
    ),
    direction: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(session),
):
    clauses = [Property.deleted.is_(False)]
    if q.strip():
        # Escape wildcard characters so a literal '%' remains searchable.
        term = (
            normalize(q).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        clauses.append(
            or_(
                *(
                    func.normalize(getattr(Property, field)).like(
                        f"%{term}%", escape="\\"
                    )
                    for field in ["address", "city", "source", "agency"]
                )
            )
        )
    if city.strip():
        clauses.append(func.normalize(Property.city) == normalize(city))
    if zone is not None:
        clauses.append(func.city_zone(Property.city) == zone)
    if source:
        clauses.append(Property.source == source)
    if status:
        clauses.append(Property.status == status)
    total = db.scalar(select(func.count()).select_from(Property).where(*clauses))
    pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, pages)
    if sort == "zone":
        field = func.city_zone(Property.city)
    elif sort == "city":
        field = func.normalize(Property.city)
    elif sort == "status":
        field = case({s: i for i, s in enumerate(STATUSES)}, value=Property.status)
    else:
        field = getattr(Property, sort)
    order = asc(field) if direction == "asc" else desc(field)
    items = db.scalars(
        select(Property)
        .where(*clauses)
        .order_by(order.nulls_last(), Property.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [serialize(item) for item in items],
        "total": total,
        "page": page,
        "pages": pages,
    }


@router.post("/properties", status_code=201)
def create_property(data: PropertyInput, db: Session = Depends(session)):
    item = Property(id=str(uuid4()), **input_values(data, db))
    db.add(item)
    record(db, item, "Création")
    commit(db)
    return serialize(item)


@router.get("/properties/{item_id}")
def detail(item_id: str, db: Session = Depends(session)):
    item = get_item(db, item_id)
    result = serialize(item)
    result["history"] = [
        {
            "action": h.action,
            "occurred_at": timestamp(h.occurred_at),
            "snapshot": h.snapshot,
        }
        for h in db.scalars(
            select(PropertyHistory)
            .where(PropertyHistory.property_id == item.id)
            .order_by(PropertyHistory.id.desc())
        )
    ]
    return result


@router.put("/properties/{item_id}")
def update_property(item_id: str, data: PropertyUpdate, db: Session = Depends(session)):
    item = get_item(db, item_id)
    if item.version != data.version:
        raise HTTPException(
            409, "Cette fiche a changé. Rechargez-la avant de réessayer."
        )
    for key, value in input_values(data, db).items():
        setattr(item, key, value)
    item.updated_at = now()
    record(db, item, "Modification")
    commit(db)
    return serialize(item)


@router.delete("/properties/{item_id}")
def delete_property(
    item_id: str,
    version: int = Query(..., ge=1),
    confirm: bool = False,
    db: Session = Depends(session),
):
    item = get_item(db, item_id)
    if not confirm:
        raise HTTPException(400, "Confirmez la suppression de ce bien.")
    if item.version != version:
        raise HTTPException(
            409, "Cette fiche a changé. Rechargez-la avant de réessayer."
        )
    # Soft deletion retains history and the local photo, avoiding irreversible loss.
    item.deleted = True
    item.updated_at = now()
    record(db, item, "Suppression")
    commit(db)
    return {
        "message": "Bien supprimé de la liste. Historique et photo conservés localement."
    }
