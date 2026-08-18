"""Inicializa la base de datos de Fitlosophy.

Crea el esquema, aplica las migraciones pendientes y, si se le dan credenciales,
da de alta el primer usuario del despliegue. Es idempotente: se puede ejecutar
sobre una base de datos ya en uso para migrarla sin tocar los datos.

Variables (del entorno o de `app/backend/.env`, ver `.env.example`):

    FITLOSOPHY_DB        ruta de la BD (opcional, por defecto ./fitlosophy.db)
    FITLOSOPHY_USER      primer usuario a crear (opcional)
    FITLOSOPHY_PASSWORD  su contraseña (opcional)

Uso:

    cd app/backend
    ./.venv/bin/python scripts/init_db.py

Los usuarios siguientes **no** se crean aquí: para eso está
`scripts/crear_usuario.py`, que pide la contraseña por terminal en vez de
leerla del `.env`. Conviene vaciar `FITLOSOPHY_PASSWORD` del `.env` en cuanto
el despliegue esté en marcha.
"""

from __future__ import annotations

import os

from _comun import abrir_bd, ejecutar

from fitlosophy_api.usuarios import alta_usuario, buscar  # noqa: E402


def main() -> int:
    conn, ruta = abrir_bd()
    print(f"Base de datos lista en {ruta} (esquema y migraciones aplicados).")

    usuario = os.environ.get("FITLOSOPHY_USER")
    password = os.environ.get("FITLOSOPHY_PASSWORD")
    if not usuario or not password:
        if not conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
            print("Todavía no hay ningún usuario: crea uno con scripts/crear_usuario.py.")
        return 0

    if buscar(conn, usuario) is not None:
        print(f"El usuario '{usuario}' ya existe; no se toca (para la contraseña, cambiar_password.py).")
        return 0

    alta_usuario(conn, usuario, password)
    print(f"Usuario '{usuario}' creado con su perfil inicial.")
    print("Vacía FITLOSOPHY_PASSWORD del .env: ya no hace falta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
