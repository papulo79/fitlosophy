"""Autenticación de usuario único (docs/14: acceso y privacidad).

- Contraseña con hash `hashlib.pbkdf2_hmac` (stdlib).
- Sesión con cookie HttpOnly firmada: token opaco almacenado en la tabla
  `auth_sessions` con expiración de 30 días (el usuario no se loguea a diario).
- Sin registro: el usuario se crea al inicializar la BD.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request, Response
from pydantic import BaseModel

COOKIE_NOMBRE = "fitlosophy_session"
DURACION_SESION_DIAS = 30
ITERACIONES_PBKDF2 = 200_000


class LoginIn(BaseModel):
    username: str
    password: str


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERACIONES_PBKDF2)
    return digest.hex(), salt.hex()


def verificar_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    digest, _ = hash_password(password, bytes.fromhex(salt_hex))
    return hmac.compare_digest(digest, hash_hex)


def crear_usuario(conn: sqlite3.Connection, username: str, password: str) -> None:
    hash_hex, salt_hex = hash_password(password)
    conn.execute(
        "INSERT INTO users (username, password_hash, salt, created_at) VALUES (?, ?, ?, ?)",
        (username, hash_hex, salt_hex, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()


def hay_usuario(conn: sqlite3.Connection) -> bool:
    return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0


def _crear_sesion(conn: sqlite3.Connection, user_id: int) -> tuple[str, datetime]:
    token = secrets.token_hex(32)
    expira = datetime.now() + timedelta(days=DURACION_SESION_DIAS)
    conn.execute(
        "INSERT INTO auth_sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, datetime.now().isoformat(timespec="seconds"), expira.isoformat(timespec="seconds")),
    )
    conn.commit()
    return token, expira


def usuario_actual(request: Request) -> dict:
    """Dependencia FastAPI: exige sesión válida en todas las rutas protegidas
    (criterio de aceptación 9)."""
    conn: sqlite3.Connection = request.app.state.db
    token = request.cookies.get(COOKIE_NOMBRE)
    if not token:
        raise HTTPException(status_code=401, detail="Sesión requerida")
    fila = conn.execute(
        "SELECT u.id, u.username, s.expires_at FROM auth_sessions s "
        "JOIN users u ON u.id = s.user_id WHERE s.token = ?",
        (token,),
    ).fetchone()
    if fila is None or datetime.fromisoformat(fila["expires_at"]) < datetime.now():
        raise HTTPException(status_code=401, detail="Sesión no válida o caducada")
    return {"id": fila["id"], "username": fila["username"]}


def login(conn: sqlite3.Connection, datos: LoginIn, response: Response) -> dict:
    fila = conn.execute("SELECT * FROM users WHERE username = ?", (datos.username,)).fetchone()
    if fila is None or not verificar_password(datos.password, fila["salt"], fila["password_hash"]):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    token, expira = _crear_sesion(conn, fila["id"])
    response.set_cookie(
        COOKIE_NOMBRE,
        token,
        max_age=DURACION_SESION_DIAS * 24 * 3600,
        httponly=True,
        samesite="lax",
        expires=expira.strftime("%a, %d %b %Y %H:%M:%S GMT"),
    )
    return {"username": fila["username"], "sesion_expira": expira.isoformat(timespec="seconds")}


def logout(conn: sqlite3.Connection, request: Request, response: Response) -> dict:
    token = request.cookies.get(COOKIE_NOMBRE)
    if token:
        conn.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
        conn.commit()
    response.delete_cookie(COOKIE_NOMBRE)
    return {"detalle": "Sesión cerrada"}


# Reexport para usar como dependencia en los routers.
SesionActual = Depends(usuario_actual)
