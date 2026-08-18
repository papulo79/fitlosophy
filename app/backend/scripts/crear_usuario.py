"""Da de alta un usuario de Fitlosophy.

No hay registro por HTTP (docs/14): las altas se hacen aquí, en el servidor.
El usuario se crea con su perfil sembrado desde `data/perfil-plantilla.yaml`
—material del lugar de entrenamiento, nada personal— y a partir de ese momento
ya puede entrar y completarlo desde la pantalla Perfil.

Uso:
    cd app/backend
    ./.venv/bin/python scripts/crear_usuario.py <usuario>

La contraseña se pide por terminal (mínimo 12 caracteres); no se pasa como
argumento ni se guarda en el `.env`. La ruta de la BD sale de `FITLOSOPHY_DB`.
"""

from __future__ import annotations

import sys

# `_comun` añade `src/` al path: los imports de fitlosophy_api van después.
from _comun import abrir_bd, ejecutar, pedir_password

from fitlosophy_api.usuarios import (  # noqa: E402
    ErrorUsuario,
    alta_usuario,
    buscar,
    validar_username,
)


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Uso: {sys.argv[0]} <usuario>", file=sys.stderr)
        return 2
    username = validar_username(sys.argv[1])

    conn, ruta = abrir_bd()
    if buscar(conn, username) is not None:
        raise ErrorUsuario(
            f"El usuario '{username}' ya existe. "
            "Para cambiarle la contraseña usa scripts/cambiar_password.py."
        )

    password = pedir_password(f"Contraseña para '{username}'")
    alta_usuario(conn, username, password)

    print(f"Usuario '{username}' creado en {ruta}.")
    print("Perfil sembrado desde data/perfil-plantilla.yaml: que lo complete desde la pantalla Perfil.")
    return 0


if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
