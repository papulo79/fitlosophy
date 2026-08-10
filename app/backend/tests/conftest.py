"""Permite ejecutar `python -m pytest` desde app/backend sin instalar el paquete."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Los tests no deben leer el `.env` del despliegue local: si el desarrollador
# activa ahí `FITLOSOPHY_COOKIE_SECURE` o baja los umbrales del login, la suite
# cambiaría de resultado según la máquina. Se apunta a un fichero inexistente.
os.environ.setdefault("FITLOSOPHY_ENV_FILE", str(Path(__file__).resolve().parent / "sin-env"))
