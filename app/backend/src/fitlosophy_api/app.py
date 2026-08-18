"""Fábrica de la aplicación FastAPI del MVP de Fitlosophy (docs/14).

Uso:
    uvicorn "fitlosophy_api.app:create_app" --factory

La ruta de la BD se configura con la variable de entorno `FITLOSOPHY_DB`
(por defecto `./fitlosophy.db`).
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI

from fitlosophy.catalog import load_default_catalog

from .config import cargar_env
from .db import conectar, crear_esquema
from .routes import router


def create_app(db_path: str | Path | None = None) -> FastAPI:
    # `.env` de app/backend: no pisa lo que ya venga del entorno (systemd, shell).
    # Con `db_path` explícito (tests) tampoco afecta a la ruta de la BD.
    cargar_env()
    ruta = db_path or os.environ.get("FITLOSOPHY_DB", "fitlosophy.db")
    # Crea el esquema y migra lo que haga falta (ver `db.crear_esquema`). El
    # perfil ya no se siembra aquí: hay uno por usuario y lo crea el alta
    # (`scripts/crear_usuario.py`), que es el único momento en que se sabe de
    # quién es.
    arranque = conectar(ruta)
    try:
        crear_esquema(arranque)
    finally:
        arranque.close()

    app = FastAPI(
        title="Fitlosophy API",
        description="API del MVP de Fitlosophy: decisión diaria, ejecución, cierre e historial (docs/14).",
        version="0.1.0",
    )
    # Cada petición abre su propia conexión desde esta ruta (ver `db.db_conn`).
    app.state.db_path = str(ruta)
    app.state.catalog = load_default_catalog()
    app.include_router(router)

    # En producción se sirve el frontend compilado si existe (app/frontend/dist).
    # El frontend usa rutas hash (#/...), así que no hace falta fallback SPA.
    # `EstaticosVersionados` añade el Cache-Control que StaticFiles no pone y
    # sin el cual el CDN sirve un index.html viejo tras cada despliegue.
    dist = Path(__file__).resolve().parents[3] / "frontend" / "dist"
    if dist.is_dir():
        from .static import EstaticosVersionados

        app.mount("/", EstaticosVersionados(directory=dist, html=True), name="frontend")
    return app
