"""Fábrica de la aplicación FastAPI del MVP de Fitlosophy (docs/14).

Uso:
    uvicorn "fitlosophy_api.app:create_app" --factory

La ruta de la BD se configura con la variable de entorno `FITLOSOPHY_DB`
(por defecto `./fitlosophy.db`).
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

from fastapi import FastAPI

from fitlosophy.catalog import load_default_catalog, load_default_perfil

from .db import cargar_json, conectar, crear_esquema, volcar_json
from .routes import router


def create_app(db_path: str | Path | None = None) -> FastAPI:
    ruta = db_path or os.environ.get("FITLOSOPHY_DB", "fitlosophy.db")
    conn = conectar(ruta)
    crear_esquema(conn)

    # Semilla del perfil editable desde data/perfil.yaml (pantalla 6 de docs/14).
    if conn.execute("SELECT COUNT(*) FROM profile").fetchone()[0] == 0:
        perfil = load_default_perfil()
        from datetime import datetime

        conn.execute(
            "INSERT INTO profile (id, data, updated_at) VALUES (1, ?, ?)",
            (volcar_json(perfil.raw), datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()

    app = FastAPI(
        title="Fitlosophy API",
        description="API del MVP de Fitlosophy: decisión diaria, ejecución, cierre e historial (docs/14).",
        version="0.1.0",
    )
    app.state.db = conn
    app.state.lock = threading.Lock()
    app.state.catalog = load_default_catalog()
    app.include_router(router)
    return app
