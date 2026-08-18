"""Alta y mantenimiento de usuarios (docs/14: acceso y privacidad).

La aplicación **no expone ninguna operación de gestión de cuentas por HTTP**:
no hay registro, ni roles, ni endpoint de administración. Las altas y las
rotaciones de contraseña se hacen a mano en el servidor con los scripts de
`scripts/`, que son quienes usan este módulo. La superficie que no existe no se
puede atacar, y con un despliegue familiar detrás de un túnel eso vale más que
la comodidad de una pantalla de administración.

`auth.py` se queda con lo que la API sí necesita en caliente: verificar la
contraseña, emitir la sesión y frenar la fuerza bruta.
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime

from fitlosophy.catalog import load_perfil_plantilla

from .auth import hash_password
from .db import volcar_json

# Mínimo para una aplicación expuesta a internet por un túnel. No se exige
# composición (mayúsculas, símbolos): la longitud es lo que de verdad importa y
# lo demás solo empuja a elegir contraseñas peores y a apuntarlas.
LONGITUD_MINIMA_PASSWORD = 12

# Identificador de acceso: sin espacios ni mayúsculas, para que no haya dudas
# al teclearlo en el móvil ni dos usuarios que se distingan por el «shift».
# Se admiten `@ . + -` porque una dirección de correo es un nombre de usuario
# perfectamente razonable, y el primer usuario del despliegue ya usa una.
PATRON_USERNAME = re.compile(r"^[a-z0-9][a-z0-9._+@-]{2,63}$")


class ErrorUsuario(Exception):
    """Error de gestión de usuarios con un mensaje pensado para la terminal."""


def validar_username(username: str) -> str:
    """Comprueba el formato de un nombre **que se va a crear**.

    No se aplica al buscar: los usuarios que ya existen valen tal cual estén
    guardados, y una consulta que rechazase su nombre por formato dejaría sin
    poder cambiar la contraseña a quien la tiene desde antes.
    """
    username = (username or "").strip()
    if not PATRON_USERNAME.match(username):
        raise ErrorUsuario(
            "El usuario debe tener entre 3 y 64 caracteres en minúscula "
            "(letras, números y . _ + - @) y empezar por letra o número."
        )
    return username


def validar_password(password: str) -> None:
    if len(password or "") < LONGITUD_MINIMA_PASSWORD:
        raise ErrorUsuario(
            f"La contraseña debe tener al menos {LONGITUD_MINIMA_PASSWORD} caracteres."
        )


def buscar(conn: sqlite3.Connection, username: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def alta_usuario(conn: sqlite3.Connection, username: str, password: str) -> int:
    """Crea el usuario y le siembra su perfil. Devuelve su id.

    El perfil sale de `data/perfil-plantilla.yaml`: lleva el material del lugar
    de entrenamiento, que se comparte, y nada personal. El perfil de un atleta
    nunca se copia a otro (docs/14).
    """
    username = validar_username(username)
    validar_password(password)
    if buscar(conn, username) is not None:
        raise ErrorUsuario(f"El usuario '{username}' ya existe.")

    ahora = datetime.now().isoformat(timespec="seconds")
    hash_hex, salt_hex = hash_password(password)
    cur = conn.execute(
        "INSERT INTO users (username, password_hash, salt, created_at) VALUES (?, ?, ?, ?)",
        (username, hash_hex, salt_hex, ahora),
    )
    user_id = int(cur.lastrowid)
    conn.execute(
        "INSERT INTO profiles (user_id, data, updated_at) VALUES (?, ?, ?)",
        (user_id, volcar_json(load_perfil_plantilla().raw), ahora),
    )
    conn.commit()
    return user_id


def cambiar_password(conn: sqlite3.Connection, username: str, password: str) -> int:
    """Cambia la contraseña e **invalida todas las sesiones** de ese usuario.

    Una contraseña se rota porque la anterior ya no es de fiar, y las cookies
    emitidas con ella durarían 30 días más. Devuelve cuántas sesiones se han
    cerrado. Solo afecta a ese usuario: los demás siguen dentro.
    """
    validar_password(password)
    fila = buscar(conn, username)
    if fila is None:
        raise ErrorUsuario(f"No existe el usuario '{username}'.")

    hash_hex, salt_hex = hash_password(password)
    conn.execute(
        "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
        (hash_hex, salt_hex, fila["id"]),
    )
    sesiones = conn.execute(
        "SELECT COUNT(*) FROM auth_sessions WHERE user_id = ?", (fila["id"],)
    ).fetchone()[0]
    conn.execute("DELETE FROM auth_sessions WHERE user_id = ?", (fila["id"],))
    # Los intentos fallidos previos tampoco deben seguir bloqueando el acceso.
    conn.execute("DELETE FROM login_failures WHERE username = ?", (username,))
    conn.commit()
    return int(sesiones)


def listar_usuarios(conn: sqlite3.Connection) -> list[dict]:
    """Usuarios con un resumen de su actividad, para revisar el despliegue."""
    filas = conn.execute(
        """
        SELECT u.id, u.username, u.created_at,
               (SELECT COUNT(*) FROM auth_sessions s
                 WHERE s.user_id = u.id AND s.expires_at >= ?)          AS sesiones_abiertas,
               (SELECT COUNT(*) FROM training_sessions t
                 WHERE t.user_id = u.id AND t.estado IN ('finalizada', 'cerrada')) AS entrenos,
               (SELECT COUNT(*) FROM bjj_records b WHERE b.user_id = u.id)         AS bjj,
               (SELECT MAX(t.fecha) FROM training_sessions t
                 WHERE t.user_id = u.id AND t.estado IN ('finalizada', 'cerrada')) AS ultimo_entreno
          FROM users u ORDER BY u.id
        """,
        (datetime.now().isoformat(timespec="seconds"),),
    ).fetchall()
    return [dict(f) for f in filas]
