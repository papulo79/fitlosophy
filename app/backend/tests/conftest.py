"""Permite ejecutar `python -m pytest` desde app/backend sin instalar el paquete."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Los tests no deben leer el `.env` del despliegue local: si el desarrollador
# activa ahí `FITLOSOPHY_COOKIE_SECURE` o baja los umbrales del login, la suite
# cambiaría de resultado según la máquina. Se apunta a un fichero inexistente.
os.environ.setdefault("FITLOSOPHY_ENV_FILE", str(Path(__file__).resolve().parent / "sin-env"))


@pytest.fixture(autouse=True)
def entorno_aislado():
    """Devuelve `os.environ` a su estado inicial después de cada test.

    `config.cargar_env` escribe en el entorno del proceso a propósito, y eso no
    lo puede deshacer `monkeypatch`: una clave que el test borró antes y el
    cargador volvió a poner se queda para el resto de la sesión. Así se coló
    `FITLOSOPHY_COOKIE_SECURE=true` desde los tests del cargador hasta los de
    la API, donde marcaba la cookie como `Secure` sobre HTTP y el cliente de
    pruebas la descartaba: los tests que venían después perdían la sesión.
    """
    original = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(original)
