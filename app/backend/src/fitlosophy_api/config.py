"""Configuración del despliegue: variables de entorno con respaldo en `.env`.

Sin dependencias nuevas (AGENTS.md): el `.env` se lee con la librería estándar.

Precedencia, de mayor a menor:

1. Variable ya presente en el entorno (systemd, shell, CI).
2. Línea del fichero `.env`.
3. Valor por defecto del código.

De este modo `FITLOSOPHY_DB=otra.db uvicorn ...` sigue ganando sobre el `.env`,
y los tests (que no cargan el fichero) no dependen del despliegue local.

El fichero vive en `app/backend/.env` y está en `.gitignore`: contiene la
contraseña del usuario único y la ruta de la BD con datos personales de salud.
El fichero `.env.example` documenta las claves sin valores reales.
"""

from __future__ import annotations

import os
from pathlib import Path

# app/backend/.env — parents: [0] fitlosophy_api, [1] src, [2] app/backend.
RUTA_ENV_POR_DEFECTO = Path(__file__).resolve().parents[2] / ".env"


def _desnudar(valor: str) -> str:
    """Quita comillas envolventes y espacios sobrantes."""
    valor = valor.strip()
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in ("'", '"'):
        return valor[1:-1]
    return valor


def cargar_env(ruta: str | Path | None = None) -> dict[str, str]:
    """Carga `ruta` (o `FITLOSOPHY_ENV_FILE`, o `app/backend/.env`) en el entorno.

    No sobrescribe variables ya definidas. Devuelve las claves aplicadas.
    Si el fichero no existe, no hace nada: el despliegue puede configurarse solo
    con variables de entorno.
    """
    if ruta is None:
        ruta = os.environ.get("FITLOSOPHY_ENV_FILE", RUTA_ENV_POR_DEFECTO)
    ruta = Path(ruta)
    if not ruta.is_file():
        return {}

    aplicadas: dict[str, str] = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        if linea.startswith("export "):
            linea = linea[len("export ") :]
        clave, sep, valor = linea.partition("=")
        clave = clave.strip()
        if not sep or not clave:
            continue  # línea malformada: se ignora en silencio
        valor = _desnudar(valor)
        if clave not in os.environ:
            os.environ[clave] = valor
            aplicadas[clave] = valor
    return aplicadas


def leer_bool(clave: str, por_defecto: bool = False) -> bool:
    valor = os.environ.get(clave)
    if valor is None:
        return por_defecto
    return valor.strip().lower() in ("1", "true", "si", "sí", "yes", "on")


def leer_int(clave: str, por_defecto: int) -> int:
    valor = os.environ.get(clave)
    if valor is None or not valor.strip():
        return por_defecto
    try:
        return int(valor)
    except ValueError:
        return por_defecto
