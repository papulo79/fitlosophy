"""Cambia la contraseña del usuario único de Fitlosophy.

`init_db.py` no la toca si el usuario ya existe (no hay registro, docs/14), así
que rotarla necesita este script. Además **invalida todas las sesiones
abiertas**: una contraseña se cambia porque la anterior ya no es de fiar, y las
cookies emitidas con ella seguirían siendo válidas 30 días.

Lee las variables del entorno o del `.env` (ver `.env.example`):

    FITLOSOPHY_USER      usuario al que cambiar la contraseña
    FITLOSOPHY_PASSWORD  contraseña nueva
    FITLOSOPHY_DB        ruta de la BD (opcional)

Uso:
    cd app/backend
    ./.venv/bin/python scripts/cambiar_password.py

Después conviene vaciar `FITLOSOPHY_PASSWORD` del `.env`: ya no hace falta y
deja de estar en el entorno del servicio.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fitlosophy_api.auth import hash_password  # noqa: E402
from fitlosophy_api.config import cargar_env  # noqa: E402
from fitlosophy_api.db import conectar, crear_esquema  # noqa: E402

LONGITUD_MINIMA = 12


def main() -> int:
    cargar_env()
    usuario = os.environ.get("FITLOSOPHY_USER")
    password = os.environ.get("FITLOSOPHY_PASSWORD")
    if not usuario or not password:
        print("Error: define FITLOSOPHY_USER y FITLOSOPHY_PASSWORD.", file=sys.stderr)
        return 1
    if len(password) < LONGITUD_MINIMA:
        print(
            f"Error: la contraseña debe tener al menos {LONGITUD_MINIMA} caracteres.",
            file=sys.stderr,
        )
        return 1

    ruta = os.environ.get("FITLOSOPHY_DB", "fitlosophy.db")
    conn = conectar(ruta)
    crear_esquema(conn)

    fila = conn.execute("SELECT id FROM users WHERE username = ?", (usuario,)).fetchone()
    if fila is None:
        print(f"Error: no existe el usuario '{usuario}'. Usa init_db.py.", file=sys.stderr)
        return 1

    hash_hex, salt_hex = hash_password(password)
    conn.execute(
        "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
        (hash_hex, salt_hex, fila["id"]),
    )
    sesiones = conn.execute("SELECT COUNT(*) FROM auth_sessions").fetchone()[0]
    conn.execute("DELETE FROM auth_sessions")
    # Los intentos fallidos previos tampoco deben seguir bloqueando el acceso.
    conn.execute("DELETE FROM login_failures")
    conn.commit()

    print(f"Contraseña de '{usuario}' actualizada.")
    print(f"Sesiones invalidadas: {sesiones} (hay que volver a entrar en todos los dispositivos).")
    print("Recuerda vaciar FITLOSOPHY_PASSWORD del .env.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
