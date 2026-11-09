from datetime import date, datetime, timezone
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def now():
    return datetime.now(timezone.utc)


class Photo(Base):
    __tablename__ = "photos"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Property(Base):
    __tablename__ = "properties"
    __table_args__ = (
        CheckConstraint("surface IS NULL OR surface >= 0", name="ck_surface"),
        CheckConstraint("energy IS NULL OR energy >= 0", name="ck_energy"),
        CheckConstraint("emissions IS NULL OR emissions >= 0", name="ck_emissions"),
        CheckConstraint(
            "dpe IS NULL OR dpe IN ('A','B','C','D','E','F','G')", name="ck_dpe"
        ),
        CheckConstraint(
            "ges IS NULL OR ges IN ('A','B','C','D','E','F','G')", name="ck_ges"
        ),
        CheckConstraint(
            "source IS NULL OR source IN ('Registre DPE','Agence immobilière')",
            name="ck_source",
        ),
        CheckConstraint(
            "status IN ('Non prospecté','Prospection prévue','Prospection impossible','Prospecté')",
            name="ck_status",
        ),
        CheckConstraint("version >= 1", name="ck_version"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    address: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str | None] = mapped_column(String(150))
    surface: Mapped[float | None] = mapped_column(Float)
    dpe: Mapped[str | None] = mapped_column(String(1))
    energy: Mapped[float | None] = mapped_column(Float)
    ges: Mapped[str | None] = mapped_column(String(1))
    emissions: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(30))
    agency: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="Non prospecté", index=True)
    next_action: Mapped[date | None] = mapped_column(Date)
    photo_id: Mapped[str | None] = mapped_column(ForeignKey("photos.id"))
    photo: Mapped[Photo | None] = relationship()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    __mapper_args__ = {"version_id_col": version}


class PropertyHistory(Base):
    __tablename__ = "property_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.id"), index=True)
    action: Mapped[str] = mapped_column(String(30))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    snapshot: Mapped[dict] = mapped_column(JSON)
