"""Inicializa la base de datos del MVP de Fitlosophy.

Crea el esquema, siembra el perfil editable desde `data/perfil.yaml` y crea el
usuario único a partir de las variables de entorno:

    FITLOSOPHY_USER      nombre de usuario (obligatoria)
    FITLOSOPHY_PASSWORD  contraseña (obligatoria)
    FITLOSOPHY_DB        ruta de la BD (opcional, por defecto ./fitlosophy.db)

Se leen del fichero `app/backend/.env` si existe (ver `.env.example`); lo que ya
esté en el entorno tiene prioridad. Uso:

    cd app/backend
    ./.venv/bin/python scripts/init_db.py                 # con .env relleno
    FITLOSOPHY_USER=... FITLOSOPHY_PASSWORD=... ./.venv/bin/python scripts/init_db.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fitlosophy.catalog import load_default_perfil  # noqa: E402
from fitlosophy_api.auth import crear_usuario, hay_usuario  # noqa: E402
from fitlosophy_api.config import cargar_env  # noqa: E402
from fitlosophy_api.db import conectar, crear_esquema, volcar_json  # noqa: E402


def main() -> int:
    cargar_env()
    usuario = os.environ.get("FITLOSOPHY_USER")
    password = os.environ.get("FITLOSOPHY_PASSWORD")
    if not usuario or not password:
        print("Error: define FITLOSOPHY_USER y FITLOSOPHY_PASSWORD.", file=sys.stderr)
        return 1

    ruta = os.environ.get("FITLOSOPHY_DB", "fitlosophy.db")
    conn = conectar(ruta)
    crear_esquema(conn)

    if conn.execute("SELECT COUNT(*) FROM profile").fetchone()[0] == 0:
        perfil = load_default_perfil()
        from datetime import datetime

        conn.execute(
            "INSERT INTO profile (id, data, updated_at) VALUES (1, ?, ?)",
            (volcar_json(perfil.raw), datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
        print("Perfil sembrado desde data/perfil.yaml.")

    if hay_usuario(conn):
        print("La base de datos ya tiene usuario; no se crea otro (sin registro, docs/14).")
    else:
        crear_usuario(conn, usuario, password)
        print(f"Usuario '{usuario}' creado.")

    print(f"Base de datos lista en {ruta}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
