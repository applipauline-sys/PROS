"""Functional UI test in an isolated temporary directory; never touches real data.
Run with Python having Playwright and Pillow installed, and Chromium available.
"""

import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request

from PIL import Image
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run():
    with tempfile.TemporaryDirectory(prefix="morny-browser-") as directory:
        directory = Path(directory)
        env = {**os.environ, "MORNY_DATA_DIR": str(directory / "data")}
        subprocess.run(
            [str(PYTHON), "-m", "alembic", "upgrade", "head"],
            cwd=ROOT / "backend",
            env=env,
            check=True,
        )
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        log = (directory / "server.log").open("w")
        server = None

        def start():
            process = subprocess.Popen(
                [
                    str(PYTHON),
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                cwd=ROOT / "backend",
                env=env,
                stdout=log,
                stderr=log,
            )
            for _ in range(100):
                try:
                    with urllib.request.urlopen(
                        url + "/api/health", timeout=1
                    ) as response:
                        if response.status == 200:
                            return process
                except OSError:
                    pass
                if process.poll() is not None:
                    raise AssertionError((directory / "server.log").read_text())
                time.sleep(0.1)
            process.terminate()
            raise AssertionError("Le serveur ne démarre pas.")

        def stop(process):
            process.terminate()
            process.wait(timeout=10)

        image_path = directory / "photo.png"
        Image.new("RGB", (160, 120), color="#586d48").save(image_path)
        try:
            server = start()
            with sync_playwright() as p:
                chromium = shutil.which("chromium") or shutil.which("google-chrome")
                browser = p.chromium.launch(
                    headless=True, **({"executable_path": chromium} if chromium else {})
                )
                page = browser.new_page(viewport={"width": 1440, "height": 1050})
                errors, external, failed = [], [], []
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.on(
                    "request",
                    lambda request: external.append(request.url)
                    if not request.url.startswith(url)
                    and not request.url.startswith("blob:")
                    else None,
                )
                page.on(
                    "response",
                    lambda response: failed.append((response.status, response.url))
                    if response.status >= 400
                    else None,
                )
                # Native confirmations are verified for both cancellation and acceptance.
                confirmations = {"accept": True}

                def confirm(dialog):
                    dialog.accept() if confirmations["accept"] else dialog.dismiss()

                page.on("dialog", confirm)
                page.goto(url + "/#mes-biens")
                page.get_by_text("Votre portefeuille commence ici").wait_for()
                page.get_by_role("button", name="Ajouter un bien").click()
                page.get_by_label("Adresse", exact=True).fill("12 avenue des Érables")
                page.get_by_label("Rechercher une commune", exact=True).fill(
                    "DEAUVILLE"
                )
                page.get_by_label("Ville", exact=True).select_option(label="Deauville")
                page.locator("dialog").get_by_text("Zone 9", exact=True).wait_for()
                page.get_by_label("Surface (m²)", exact=True).fill("85.5")
                page.get_by_label("Classe DPE", exact=True).select_option("C")
                page.get_by_label("Consommation (kWh/m²/an)", exact=True).fill("130")
                page.get_by_label("Classe GES", exact=True).select_option("B")
                page.get_by_label("Émissions (kg CO₂e/m²/an)", exact=True).fill("15")
                page.get_by_label("Source", exact=True).last.select_option(
                    "Agence immobilière"
                )
                page.get_by_label("Nom de l’agence", exact=True).fill(
                    "Morny Immobilier"
                )
                page.get_by_label("Statut", exact=True).select_option(
                    "Prospection prévue"
                )
                page.get_by_label("Date de prochaine action", exact=True).fill(
                    "2026-12-12"
                )
                page.get_by_label("Notes", exact=True).fill(
                    "Note de test, sans coordonnées personnelles"
                )
                page.locator("input[type=file]").set_input_files(str(image_path))
                page.get_by_role("button", name="Enregistrer", exact=True).click()
                page.get_by_role(
                    "button", name="12 avenue des Érables", exact=True
                ).wait_for()
                assert page.locator("tbody img").evaluate(
                    "(img) => img.complete && img.naturalWidth > 0"
                )
                page.get_by_role(
                    "button", name="12 avenue des Érables", exact=True
                ).click()
                page.get_by_role("heading", name="Fiche du bien", exact=True).wait_for()
                page.get_by_text(
                    "Note de test, sans coordonnées personnelles", exact=True
                ).first.wait_for()
                page.get_by_role("button", name="Modifier la fiche").click()
                page.get_by_label("Rechercher une commune", exact=True).fill("")
                page.get_by_label("Ville", exact=True).select_option("__other")
                page.get_by_label("Autre ville", exact=True).fill(
                    "  saint-andre-d'hebertot  "
                )
                page.locator("dialog").get_by_text("Zone 5", exact=True).wait_for()
                page.get_by_role("button", name="Enregistrer", exact=True).click()
                page.locator("tbody").get_by_text(
                    "Saint-André-d'Hébertot", exact=True
                ).wait_for()
                page.get_by_role(
                    "button", name="12 avenue des Érables", exact=True
                ).click()
                expect(page.locator(".property-history details")).to_have_count(2)
                confirmations["accept"] = False
                page.get_by_role("button", name="Supprimer", exact=True).click()
                assert page.get_by_role("heading", name="Fiche du bien").is_visible()
                confirmations["accept"] = True
                page.get_by_role("button", name="Fermer la fiche").click()
                # Restart the actual API process, then verify the saved property/photo from the UI.
                stop(server)
                server = start()
                page.reload()
                page.get_by_role(
                    "button", name="12 avenue des Érables", exact=True
                ).wait_for()
                assert page.locator("tbody img").evaluate(
                    "(img) => img.complete && img.naturalWidth > 0"
                )
                page.get_by_role("button", name="Filtres", exact=True).click()
                page.get_by_label("Zone", exact=True).select_option("5")
                page.get_by_label("Statut", exact=True).select_option(
                    "Prospection prévue"
                )
                page.get_by_label("Source", exact=True).select_option(
                    "Agence immobilière"
                )
                page.get_by_label("Rechercher un bien", exact=True).fill("ERABLES")
                page.get_by_role(
                    "button", name="12 avenue des Érables", exact=True
                ).wait_for()
                page.get_by_label("Rechercher un bien", exact=True).fill("introuvable")
                page.get_by_text("Aucun résultat", exact=True).wait_for()
                page.get_by_role(
                    "button", name="Effacer les critères", exact=True
                ).click()
                page.get_by_role(
                    "button", name="12 avenue des Érables", exact=True
                ).wait_for()
                page.get_by_role(
                    "checkbox", name="Sélectionner les biens de cette page"
                ).check()
                page.get_by_text("La sélection est préparée", exact=False).wait_for()
                page.screenshot(path="/tmp/morny-biens-desktop.png", full_page=True)
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= window.innerWidth"
                )
                page.get_by_role(
                    "button", name="12 avenue des Érables", exact=True
                ).click()
                page.get_by_role("button", name="Modifier la fiche").click()
                assert page.locator("dialog").evaluate(
                    "(dialog) => dialog.scrollWidth <= dialog.clientWidth"
                )
                page.screenshot(path="/tmp/morny-bien-mobile.png", full_page=True)
                page.get_by_label("Adresse", exact=True).fill("Changement abandonné")
                page.get_by_role("button", name="Annuler", exact=True).click()
                page.get_by_role(
                    "button", name="12 avenue des Érables", exact=True
                ).click()
                page.get_by_role("button", name="Supprimer", exact=True).click()
                page.get_by_text(
                    "Votre portefeuille commence ici", exact=True
                ).wait_for()
                # Verify pagination on a realistic multi-page result, using isolated test data.
                for number in range(27):
                    response = page.request.post(
                        url + "/api/properties",
                        data={"address": f"Bien test {number:02d}", "city": "Lisieux"},
                    )
                    assert response.status == 201
                page.reload()
                page.get_by_text("Page 1 sur 2", exact=True).wait_for()
                assert page.locator("tbody tr").count() == 25
                page.get_by_role("button", name="Page suivante").click()
                page.get_by_text("Page 2 sur 2", exact=True).wait_for()
                assert page.locator("tbody tr").count() == 2
                # Existing navigation remains usable.
                for title in [
                    "Tableau de bord",
                    "Calendrier",
                    "Zones de prospection",
                    "Statistiques",
                    "Paramètres",
                ]:
                    page.get_by_role("link", name=title, exact=True).click()
                    page.get_by_role(
                        "heading", name=title, exact=True, level=1
                    ).wait_for()
                # A lost local connection must produce a readable French message and recover.
                page.route("**/api/properties?*", lambda route: route.abort())
                page.get_by_role("link", name="Mes biens", exact=True).click()
                page.get_by_text(
                    "Connexion au serveur local impossible.", exact=False
                ).wait_for()
                page.unroute("**/api/properties?*")
                page.get_by_role("button", name="Réessayer", exact=True).click()
                expect(page.locator("tbody tr")).to_have_count(25)
                assert not errors, errors
                assert not external, external
                assert not failed, failed
                browser.close()
                print(
                    "PASS navigateur : création complète, photo, fiche, édition, ville libre et zone, historique, annulation, suppression confirmée, redémarrage, recherche/filtres, sélection, pagination, mobile, navigation existante et récupération après coupure simulée ; zéro erreur JS/HTTP et zéro requête externe."
                )
        finally:
            if server is not None and server.poll() is None:
                stop(server)
            log.close()


if __name__ == "__main__":
    run()
