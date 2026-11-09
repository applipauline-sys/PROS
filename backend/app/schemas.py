from datetime import date
from typing import Annotated, Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

Status = Literal[
    "Non prospecté", "Prospection prévue", "Prospection impossible", "Prospecté"
]
Source = Literal["Registre DPE", "Agence immobilière"]
Letter = Literal["A", "B", "C", "D", "E", "F", "G"]
Positive = Annotated[float, Field(ge=0, le=1_000_000_000, allow_inf_nan=False)]


class PropertyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    address: Annotated[str, StringConstraints(max_length=500)] | None = None
    city: Annotated[str, StringConstraints(max_length=150)] | None = None
    surface: Positive | None = None
    dpe: Letter | None = None
    energy: Positive | None = None
    ges: Letter | None = None
    emissions: Positive | None = None
    source: Source | None = None
    agency: Annotated[str, StringConstraints(max_length=200)] | None = None
    notes: Annotated[str, StringConstraints(max_length=10000)] | None = None
    status: Status = "Non prospecté"
    next_action: date | None = None
    photo_id: Annotated[str, StringConstraints(max_length=36)] | None = None

    @field_validator("address", "city", "agency", "notes", mode="before")
    @classmethod
    def blanks(cls, value):
        return (value.strip() or None) if isinstance(value, str) else value

    @model_validator(mode="after")
    def agency_source(self):
        if self.source != "Agence immobilière":
            self.agency = None
        return self


class PropertyUpdate(PropertyInput):
    version: int = Field(ge=1)
