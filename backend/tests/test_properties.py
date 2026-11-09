from io import BytesIO
import os
from pathlib import Path
import subprocess
import sys
import pytest
from PIL import Image
from sqlalchemy import text
from app.database import DATA_DIR, engine
from app.zones import CITIES, ZONES, resolve_city


def create(client, **values):
    response = client.post("/api/properties", json=values)
    assert response.status_code == 201, response.text
    return response.json()


def test_optional_fields_and_no_owner_coordinates(client):
    item = create(client)
    assert item["city"] is None and item["surface"] is None
    assert item["status"] == "Non prospecté"
    assert item["zone"]["id"] == 0
    assert item["created_at"] and item["updated_at"]
    assert client.get("/api/properties").json()["total"] == 1
    assert (
        client.post("/api/properties", json={"owner_phone": "0123456789"}).status_code
        == 422
    )


def test_edit_history_confirmation_delete_and_conflict(client):
    item = create(client, city="Lisieux", address="  8 rue de la Paix  ", surface=0)
    before = client.get("/api/properties/" + item["id"]).json()
    assert before["history"][0]["action"] == "Création"
    assert before["address"] == "8 rue de la Paix"
    update = {
        "city": " DEAUVILLE ",
        "version": item["version"],
        "source": "Agence immobilière",
        "agency": "Morny",
        "status": "Prospection prévue",
        "next_action": "2026-12-10",
    }
    changed = client.put("/api/properties/" + item["id"], json=update)
    assert changed.status_code == 200, changed.text
    changed = changed.json()
    assert changed["city"] == "Deauville" and changed["zone"]["id"] == 9
    assert changed["created_at"] == before["created_at"]
    assert changed["updated_at"] >= before["updated_at"]
    assert client.put("/api/properties/" + item["id"], json=update).status_code == 409
    history = client.get("/api/properties/" + item["id"]).json()["history"]
    assert len(history) == 2 and history[1]["snapshot"]["city"] == "Lisieux"
    assert (
        client.delete("/api/properties/" + item["id"] + "?version=2").status_code == 400
    )
    assert (
        client.delete(
            "/api/properties/" + item["id"] + "?confirm=true&version=1"
        ).status_code
        == 409
    )
    assert (
        client.delete(
            "/api/properties/" + item["id"] + "?confirm=true&version=2"
        ).status_code
        == 200
    )
    assert client.get("/api/properties/" + item["id"]).status_code == 404
    assert client.get("/api/properties").json()["total"] == 0
    with engine.connect() as connection:
        assert connection.scalar(text("select count(*) from property_history")) == 3
        assert connection.scalar(text("select deleted from properties")) == 1


EXPECTED = [
    ["Lisieux"],
    [
        "Rocques",
        "Fauguernon",
        "Saint-Philbert-des-Champs",
        "Norolles",
        "Ouilly-le-Vicomte",
    ],
    [
        "Hermival-les-Vaux",
        "Firfol",
        "Ouilly-du-Houley",
        "Fumichon",
        "Moyaux",
        "Le Pin",
        "Le Faulq",
        "Le Brevedent",
    ],
    [
        "Blangy-le-Château",
        "Bonneville-la-Louvet",
        "Manneville-la-Pipard",
        "Fierville-les-Parcs",
    ],
    ["Saint-Julien-sur-Calonne", "Les Authieux-sur-Calonne", "Saint-André-d'Hébertot"],
    [
        "Pierrefitte-en-Auge",
        "Saint-Hymer",
        "Le Breuil-en-Auge",
        "Le Torquesne",
        "Coquainvilliers",
    ],
    ["Manerbe", "Formentin", "Le Fournet", "Auvillars", "Bonnebosq"],
    [
        "Cormeilles",
        "Saint-Pierre-de-Cormeilles",
        "Saint-Sylvestre-de-Cormeilles",
        "Le Bois-Hellain",
        "Asnières",
    ],
    ["Deauville", "Trouville-sur-Mer"],
]


@pytest.mark.parametrize(
    "zone,city", [(i, city) for i, cities in enumerate(EXPECTED, 1) for city in cities]
)
def test_exact_city_assignments(zone, city):
    assert resolve_city(city)[1] == zone


def test_zone_normalization_and_config(client):
    assert [zone["cities"] for zone in ZONES] == EXPECTED
    assert len({zone["color"] for zone in ZONES}) == 9
    item = create(client, city="  SAINT-ANDRE-D'HEBERTOT  ")
    assert item["city"] == "Saint-André-d'Hébertot" and item["zone"]["id"] == 5
    assert create(client, city="  le   breuil-en-auge ")["zone"]["id"] == 6
    assert create(client, city="Paris")["zone"]["name"] == "Hors zone"
    assert create(client, city="   ")["city"] is None
    options = client.get("/api/property-options").json()
    assert options["cities"] == CITIES and len(options["zones"]) == 10


def test_search_combined_filters_sort_and_pagination(client):
    create(
        client,
        city="Deauville",
        address="Villa des Érables",
        source="Agence immobilière",
        agency="Agence Morny",
        status="Prospecté",
        next_action="2026-12-01",
    )
    create(
        client,
        city="Trouville-sur-Mer",
        address="12 rue des Érables",
        source="Registre DPE",
    )
    create(client, city="Lisieux", address="100% calme", source="Registre DPE")
    assert (
        client.get(
            "/api/properties?q=ERABLES&zone=9&status=Prospecté&source=Agence immobilière"
        ).json()["total"]
        == 1
    )
    assert client.get("/api/properties?q=agence morny").json()["total"] == 1
    assert client.get("/api/properties?city=  DEAUVILLE ").json()["total"] == 1
    assert client.get("/api/properties?q=100%25").json()["total"] == 1
    page = client.get(
        "/api/properties?sort=city&direction=asc&page_size=1&page=2"
    ).json()
    assert (
        page["total"] == 3
        and page["pages"] == 3
        and page["items"][0]["city"] == "Lisieux"
    )
    assert (
        client.get("/api/properties?sort=zone&direction=asc").json()["items"][0]["city"]
        == "Lisieux"
    )
    assert (
        client.get("/api/properties?sort=status&direction=desc").json()["items"][0][
            "status"
        ]
        == "Prospecté"
    )
    assert (
        client.get("/api/properties?sort=next_action&direction=asc").json()["items"][0][
            "city"
        ]
        == "Deauville"
    )
    assert client.get("/api/properties?page=999&page_size=1").json()["page"] == 3
    assert client.get("/api/properties?sort=unknown").status_code == 422
    assert client.get("/api/properties?page_size=1000").status_code == 422


@pytest.mark.parametrize(
    "invalid",
    [
        {"surface": -1},
        {"energy": -2},
        {"emissions": -3},
        {"dpe": "H"},
        {"ges": "Z"},
        {"status": "Autre"},
        {"source": "Web"},
        {"next_action": "2026-02-30"},
        {"address": "x" * 501},
        {"notes": "x" * 10001},
        {"photo_id": "inconnu"},
    ],
)
def test_validation(client, invalid):
    assert client.post("/api/properties", json=invalid).status_code == 422
    assert client.get("/api/properties").json()["total"] == 0


def png():
    image = BytesIO()
    Image.new("RGB", (100, 80), color="green").save(image, format="PNG")
    return image.getvalue()


def test_upload_display_replace_remove_and_retention(client):
    upload = client.post(
        "/api/photos", content=png(), headers={"content-type": "image/png"}
    )
    assert upload.status_code == 201, upload.text
    photo = upload.json()
    assert (DATA_DIR / "photos" / (photo["id"] + ".jpg")).exists()
    display = client.get(photo["url"])
    assert (
        display.status_code == 200 and display.headers["content-type"] == "image/jpeg"
    )
    assert Image.open(BytesIO(display.content)).size == (100, 80)
    item = create(client, photo_id=photo["id"])
    assert item["photo_url"] == photo["url"]
    other = client.post(
        "/api/photos", content=png(), headers={"content-type": "image/png"}
    ).json()
    assert (
        client.put(
            "/api/properties/" + item["id"],
            json={"version": 1, "photo_id": other["id"]},
        ).json()["photo_id"]
        == other["id"]
    )
    assert (
        client.put(
            "/api/properties/" + item["id"], json={"version": 2, "photo_id": None}
        ).json()["photo_url"]
        is None
    )
    history = client.get("/api/properties/" + item["id"]).json()["history"]
    assert history[-1]["snapshot"]["photo_url"] == photo["url"]
    assert client.get(photo["url"]).status_code == 200
    assert (
        client.post(
            "/api/photos", content=b"<script/>", headers={"content-type": "image/png"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/photos", content=b"<svg/>", headers={"content-type": "image/svg+xml"}
        ).status_code
        == 415
    )
    assert (
        client.post(
            "/api/photos",
            content=b"x" * (5 * 1024 * 1024 + 1),
            headers={"content-type": "image/jpeg"},
        ).status_code
        == 413
    )


def test_agency_and_nulls(client):
    item = create(
        client,
        source="Agence immobilière",
        agency="Morny",
        dpe="A",
        ges="B",
        energy=0,
        emissions=0,
    )
    assert item["energy"] == 0 and item["emissions"] == 0
    updated = client.put(
        "/api/properties/" + item["id"],
        json={"version": 1, "source": "Registre DPE", "agency": "obsolete"},
    ).json()
    assert updated["agency"] is None and updated["dpe"] is None


def test_persistence_new_process(client):
    photo = client.post(
        "/api/photos", content=png(), headers={"content-type": "image/png"}
    ).json()
    item = create(
        client, city="Asnières", photo_id=photo["id"], notes="Conserver cette note"
    )
    code = """
import json, sys
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as client:
    item = client.get('/api/properties/'+sys.argv[1]).json()
    assert item['notes'] == 'Conserver cette note'
    assert item['zone']['id'] == 8
    assert len(item['history']) == 1
    assert client.get(item['photo_url']).status_code == 200
"""
    subprocess.run(
        [sys.executable, "-c", code, item["id"]],
        cwd=Path(__file__).resolve().parents[1],
        env=os.environ.copy(),
        check=True,
    )
