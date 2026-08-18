"""Utilidades compartidas por los scripts de gestión (docs/14).

Los scripts se ejecutan por SSH en el servidor, así que la contraseña se pide
por terminal con `getpass` y **no** se pasa como argumento: `argv` es visible
para cualquier proceso de la máquina (`ps`), y un `.env` con las contraseñas de
la familia dentro es exactamente lo que no queremos.
"""

from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from fitlosophy_api.config import cargar_env  # noqa: E402
from fitlosophy_api.db import conectar, crear_esquema  # noqa: E402
from fitlosophy_api.usuarios import ErrorUsuario, validar_password  # noqa: E402


def abrir_bd():
    """Conexión a la BD del despliegue, con el esquema al día."""
    cargar_env()
    ruta = os.environ.get("FITLOSOPHY_DB", "fitlosophy.db")
    conn = conectar(ruta)
    crear_esquema(conn)
    return conn, ruta


def pedir_password(prompt: str = "Contraseña") -> str:
    """Pide la contraseña dos veces por terminal y comprueba que coinciden.

    Si no hay terminal (cron, pipe) se acepta `FITLOSOPHY_PASSWORD` como salida
    de emergencia, avisando: sirve para automatizar el primer arranque de un
    despliegue nuevo, no para el uso diario.
    """
    if not sys.stdin.isatty():
        password = os.environ.get("FITLOSOPHY_PASSWORD")
        if not password:
            raise ErrorUsuario(
                "Sin terminal interactiva no se puede pedir la contraseña. "
                "Ejecuta el script por SSH o define FITLOSOPHY_PASSWORD."
            )
        print("Aviso: usando FITLOSOPHY_PASSWORD del entorno (no hay terminal).", file=sys.stderr)
        validar_password(password)
        return password

    password = getpass.getpass(f"{prompt}: ")
    validar_password(password)
    if password != getpass.getpass(f"{prompt} (otra vez): "):
        raise ErrorUsuario("Las contraseñas no coinciden.")
    return password


def ejecutar(main) -> int:
    """Envuelve el `main` de un script: los errores de gestión salen como un
    mensaje claro y código 1, no como una traza."""
    try:
        return main()
    except ErrorUsuario as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelado.", file=sys.stderr)
        return 130
