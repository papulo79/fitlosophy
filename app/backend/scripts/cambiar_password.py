"""Cambia la contraseña de un usuario de Fitlosophy.

Además **invalida todas las sesiones abiertas de ese usuario**: una contraseña
se cambia porque la anterior ya no es de fiar, y las cookies emitidas con ella
seguirían siendo válidas 30 días. Los demás usuarios no se ven afectados.

Uso:
    cd app/backend
    ./.venv/bin/python scripts/cambiar_password.py <usuario>

La contraseña nueva se pide por terminal (mínimo 12 caracteres); no se pasa
como argumento ni se guarda en el `.env`.
"""

from __future__ import annotations

import sys

from _comun import abrir_bd, ejecutar, pedir_password

from fitlosophy_api.usuarios import ErrorUsuario, buscar, cambiar_password  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Uso: {sys.argv[0]} <usuario>", file=sys.stderr)
        return 2
    # Sin validar el formato: es una búsqueda, no un alta. Los usuarios creados
    # antes de que existiera el patrón valen tal cual estén guardados.
    username = sys.argv[1].strip()

    conn, _ = abrir_bd()
    if buscar(conn, username) is None:
        raise ErrorUsuario(f"No existe el usuario '{username}'. Créalo con scripts/crear_usuario.py.")

    password = pedir_password(f"Contraseña nueva para '{username}'")
    sesiones = cambiar_password(conn, username, password)

    print(f"Contraseña de '{username}' actualizada.")
    print(f"Sesiones invalidadas: {sesiones} (tiene que volver a entrar en todos sus dispositivos).")
    return 0


if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
