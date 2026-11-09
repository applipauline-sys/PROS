"""Lanceur local : python demarrer.py. Arrêt : Ctrl+C."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
python = ROOT / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
if not python.exists() or not (ROOT / 'frontend/dist/index.html').exists():
    sys.exit("Installation manquante. Consultez les instructions du fichier README.md.")
try:
    subprocess.run([str(python), '-m', 'alembic', 'upgrade', 'head'], cwd=ROOT / 'backend', check=True)
    print('MORNY IMMOBILIER : ouvrez http://127.0.0.1:8000 — arrêt : Ctrl+C', flush=True)
    subprocess.run([str(python), '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], cwd=ROOT / 'backend', check=True)
except KeyboardInterrupt:
    print('\nApplication arrêtée. Vos données sont conservées.')
except subprocess.CalledProcessError as error:
    sys.exit(f"Démarrage impossible (code {error.returncode}). Consultez le message ci-dessus.")
