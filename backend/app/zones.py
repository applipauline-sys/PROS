"""Single editable source for cities, colors and automatic zone assignment."""

import json
import unicodedata
from pathlib import Path


def normalize(value: str | None) -> str:
    plain = unicodedata.normalize("NFKD", value or "")
    return " ".join(
        "".join(c for c in plain if not unicodedata.combining(c)).casefold().split()
    )


ZONES = json.loads(
    (Path(__file__).parent / "config/zones.json").read_text(encoding="utf-8")
)
CITY_INDEX = {}
for zone in ZONES:
    for city in zone["cities"]:
        key = normalize(city)
        if key in CITY_INDEX:
            raise ValueError(f"Commune déclarée deux fois : {city}")
        CITY_INDEX[key] = (city, zone["id"])
CITIES = sorted((city for city, _ in CITY_INDEX.values()), key=normalize)


def resolve_city(city: str | None) -> tuple[str | None, int]:
    if not city or not city.strip():
        return None, 0
    return CITY_INDEX.get(normalize(city), (" ".join(city.split()), 0))
