"""Autenticación (docs/14: acceso y privacidad).

- Contraseña con hash `hashlib.pbkdf2_hmac` (stdlib).
- Sesión con cookie HttpOnly: token opaco almacenado en la tabla
  `auth_sessions` con expiración de 30 días (el usuario no se loguea a diario).
- Sin registro por HTTP: las altas se hacen en el servidor (ver `usuarios.py`).
- Freno de fuerza bruta en el login: la app queda expuesta a internet por un
  túnel, y unas pocas cuentas sin límite de intentos son el punto débil
  evidente. Ver `_comprobar_freno`.
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import os
import secrets
import sqlite3
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request, Response
from pydantic import BaseModel

from .config import leer_int
from .db import db_conn

COOKIE_NOMBRE = "fitlosophy_session"
DURACION_SESION_DIAS = 30
ITERACIONES_PBKDF2 = 200_000

# --- Freno de fuerza bruta (configurable por .env) --------------------------
# Umbral por IP: fallos dentro de la ventana que disparan el bloqueo.
MAX_INTENTOS_IP = 5
# Umbral por usuario: fallos contra una misma cuenta, vengan de donde vengan.
# El límite por IP no ve el ataque repartido entre muchas direcciones contra
# una sola cuenta, que es justo el que va a por una contraseña concreta.
#
# El precio es que quien conozca un nombre de usuario puede dejar a esa persona
# sin entrar durante el bloqueo. Por eso el umbral es el doble que el de IP: en
# un despliegue familiar detrás de un túnel privado, frenar el ataque
# distribuido compensa ese riesgo, y el afectado sabe a quién preguntar.
MAX_INTENTOS_USUARIO = 10
# Ventana de conteo, en minutos: también es la memoria del bloqueo, porque al
# expirar la ventana los fallos dejan de contar.
VENTANA_MIN = 15
# Duración del primer bloqueo; se duplica por cada tanda de fallos del día.
BLOQUEO_BASE_MIN = 15
BLOQUEO_MAX_MIN = 60
# Umbral global (todas las IPs juntas): frena un ataque distribuido. Muy por
# encima del uso normal para que un despiste del usuario no lo dispare.
MAX_INTENTOS_GLOBAL = 50
# Los fallos se conservan 48 h: 24 h alimentan el escalado del bloqueo y el
# resto es margen antes de la purga.
RETENCION_FALLOS_H = 48
# Peers autorizados a declarar la IP de origen con `CF-Connecting-IP`: loopback
# y la red bridge de Docker, donde corre el contenedor de cloudflared.
PROXIES_CONFIABLES_POR_DEFECTO = "127.0.0.1,::1,172.17.0.0/16"


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


def _crear_sesion(conn: sqlite3.Connection, user_id: int) -> tuple[str, datetime]:
    token = secrets.token_hex(32)
    expira = datetime.now() + timedelta(days=DURACION_SESION_DIAS)
    conn.execute(
        "INSERT INTO auth_sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, datetime.now().isoformat(timespec="seconds"), expira.isoformat(timespec="seconds")),
    )
    conn.commit()
    return token, expira


def usuario_actual(request: Request, conn: sqlite3.Connection = Depends(db_conn)) -> dict:
    """Dependencia FastAPI: exige sesión válida en todas las rutas protegidas
    (criterio de aceptación 9).

    Devuelve `{"id", "username"}`. El `id` es lo que usa cada endpoint para
    filtrar sus consultas: sin él no hay aislamiento (criterio 10).
    """
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


def _es_proxy_confiable(host: str | None) -> bool:
    """¿Viene la petición de un proxy autorizado a declarar la IP de origen?

    La lista admite direcciones, redes CIDR y literales (para casos que no son
    una IP, como el `testclient` de los tests).
    """
    if not host:
        return False
    lista = os.environ.get("FITLOSOPHY_PROXIES_CONFIABLES", PROXIES_CONFIABLES_POR_DEFECTO)
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    for entrada in lista.split(","):
        entrada = entrada.strip()
        if not entrada:
            continue
        if entrada == host:  # literal
            return True
        if ip is None:
            continue
        try:
            if "/" in entrada:
                if ip in ipaddress.ip_network(entrada, strict=False):
                    return True
            elif ip == ipaddress.ip_address(entrada):
                return True
        except ValueError:
            continue
    return False


def ip_cliente(request: Request) -> str:
    """IP real del cliente, para el freno de fuerza bruta.

    Cloudflare sobrescribe `CF-Connecting-IP` con la IP de origen, así que es
    fiable... pero solo si la petición viene del túnel. Como el servicio escucha
    también en la LAN, esa cabecera se ignora cuando el peer no está en
    `FITLOSOPHY_PROXIES_CONFIABLES`: si no, bastaría con ir cambiándola a mano
    desde la red local para tener intentos ilimitados.
    """
    peer = request.client.host if request.client else None
    cf = request.headers.get("cf-connecting-ip")
    if cf and _es_proxy_confiable(peer):
        return cf.split(",")[0].strip()
    return peer or "desconocida"


def _cookie_segura(request: Request) -> bool:
    """¿Marcar la cookie de sesión como `Secure`?

    Con «auto» (recomendado) se decide por el esquema de la petición: `Secure`
    por HTTPS (el túnel) y sin `Secure` por HTTP (la LAN), porque el navegador
    descarta una cookie `Secure` servida por HTTP y el login no funcionaría. El
    esquema real llega vía `X-Forwarded-Proto` gracias a `--proxy-headers`.
    """
    valor = os.environ.get("FITLOSOPHY_COOKIE_SECURE", "auto").strip().lower()
    if valor in ("", "auto"):
        return request.url.scheme == "https"
    return valor in ("1", "true", "si", "sí", "yes", "on")


def _registrar_fallo(conn: sqlite3.Connection, ip: str, username: str, ahora: datetime) -> None:
    conn.execute(
        "INSERT INTO login_failures (ip, username, ts) VALUES (?, ?, ?)",
        (ip, username, ahora.isoformat(timespec="seconds")),
    )
    conn.execute(
        "DELETE FROM login_failures WHERE ts < ?",
        ((ahora - timedelta(hours=RETENCION_FALLOS_H)).isoformat(timespec="seconds"),),
    )
    conn.commit()


def _contar_fallos(
    conn: sqlite3.Connection,
    desde: datetime,
    ip: str | None = None,
    username: str | None = None,
) -> tuple[int, datetime | None]:
    """Fallos desde `desde` y fecha del último.

    Sin `ip` ni `username` cuenta todos (umbral global). Con uno de los dos,
    solo los de esa IP o los dirigidos a esa cuenta.
    """
    sql = "SELECT COUNT(*) AS n, MAX(ts) AS ultimo FROM login_failures WHERE ts >= ?"
    params: tuple = (desde.isoformat(timespec="seconds"),)
    if ip is not None:
        sql += " AND ip = ?"
        params += (ip,)
    if username is not None:
        sql += " AND username = ?"
        params += (username,)
    fila = conn.execute(sql, params).fetchone()
    ultimo = datetime.fromisoformat(fila["ultimo"]) if fila["ultimo"] else None
    return fila["n"], ultimo


def _comprobar_freno(conn: sqlite3.Connection, ip: str, username: str, ahora: datetime) -> None:
    """Rechaza con 429 si la IP, la cuenta o el conjunto han agotado intentos.

    Tres niveles, cada uno para un ataque distinto:

    - Por IP: `MAX_INTENTOS_IP` fallos en `VENTANA_MIN` bloquean esa IP. La
      duración parte de `BLOQUEO_BASE_MIN` y se duplica por cada tanda de
      fallos acumulada en 24 h, con techo en `BLOQUEO_MAX_MIN`, de modo que
      insistir sale cada vez más caro.
    - Por usuario: `MAX_INTENTOS_USUARIO` fallos contra la misma cuenta, con el
      mismo escalado. Cubre el ataque repartido entre muchas IPs contra una
      contraseña concreta, que el límite por IP no vería.
    - Global: `MAX_INTENTOS_GLOBAL` fallos en la ventana frenan el login desde
      cualquier IP. Cubre el barrido distribuido contra cuentas distintas, que
      tampoco dispara ninguno de los dos anteriores.

    Los intentos rechazados aquí no se registran como fallo: así un refresco
    del usuario legítimo no alarga su propio bloqueo.
    """
    max_ip = leer_int("FITLOSOPHY_LOGIN_MAX_INTENTOS", MAX_INTENTOS_IP)
    max_usuario = leer_int("FITLOSOPHY_LOGIN_MAX_USUARIO", MAX_INTENTOS_USUARIO)
    ventana = leer_int("FITLOSOPHY_LOGIN_VENTANA_MIN", VENTANA_MIN)
    bloqueo_base = leer_int("FITLOSOPHY_LOGIN_BLOQUEO_MIN", BLOQUEO_BASE_MIN)
    bloqueo_max = leer_int("FITLOSOPHY_LOGIN_BLOQUEO_MAX_MIN", BLOQUEO_MAX_MIN)
    max_global = leer_int("FITLOSOPHY_LOGIN_MAX_GLOBAL", MAX_INTENTOS_GLOBAL)

    inicio_ventana = ahora - timedelta(minutes=ventana)
    inicio_dia = ahora - timedelta(hours=24)

    def _frenar(maximo: int, motivo: str, **filtro) -> None:
        """Bloquea si se ha alcanzado `maximo` fallos, con el escalado por
        tandas acumuladas en 24 h."""
        fallos, ultimo = _contar_fallos(conn, inicio_ventana, **filtro)
        if fallos < maximo or ultimo is None:
            return
        fallos_dia, _ = _contar_fallos(conn, inicio_dia, **filtro)
        nivel = max(1, fallos_dia // maximo)
        minutos = min(bloqueo_base * (2 ** (nivel - 1)), bloqueo_max)
        _rechazar(ultimo + timedelta(minutes=minutos), ahora, motivo)

    _frenar(max_ip, "Demasiados intentos fallidos", ip=ip)
    if username:
        _frenar(max_usuario, "Demasiados intentos fallidos para este usuario", username=username)

    fallos_todos, ultimo_todos = _contar_fallos(conn, inicio_ventana)
    if fallos_todos >= max_global and ultimo_todos is not None:
        _rechazar(
            ultimo_todos + timedelta(minutes=bloqueo_base),
            ahora,
            "Acceso temporalmente suspendido por actividad sospechosa",
        )


def _rechazar(desbloqueo: datetime, ahora: datetime, motivo: str) -> None:
    restante = int((desbloqueo - ahora).total_seconds())
    if restante <= 0:
        return  # el bloqueo ya expiró: se deja pasar
    minutos = max(1, round(restante / 60))
    raise HTTPException(
        status_code=429,
        detail=f"{motivo}. Vuelve a intentarlo en {minutos} min.",
        headers={"Retry-After": str(restante)},
    )


def login(
    conn: sqlite3.Connection, datos: LoginIn, request: Request, response: Response
) -> dict:
    ahora = datetime.now()
    ip = ip_cliente(request)
    _comprobar_freno(conn, ip, datos.username, ahora)

    fila = conn.execute("SELECT * FROM users WHERE username = ?", (datos.username,)).fetchone()
    if fila is None or not verificar_password(datos.password, fila["salt"], fila["password_hash"]):
        _registrar_fallo(conn, ip, datos.username, ahora)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    # Acierto: ni esa IP ni esa cuenta arrastran los fallos previos. Limpiar
    # ambos evita que un despiste propio deje al usuario a un intento del
    # bloqueo durante el resto de la ventana.
    conn.execute("DELETE FROM login_failures WHERE ip = ? OR username = ?", (ip, datos.username))
    conn.commit()

    token, expira = _crear_sesion(conn, fila["id"])
    response.set_cookie(
        COOKIE_NOMBRE,
        token,
        max_age=DURACION_SESION_DIAS * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=_cookie_segura(request),
        expires=expira.strftime("%a, %d %b %Y %H:%M:%S GMT"),
    )
    return {"username": fila["username"], "sesion_expira": expira.isoformat(timespec="seconds")}


def logout(conn: sqlite3.Connection, request: Request, response: Response) -> dict:
    token = request.cookies.get(COOKIE_NOMBRE)
    if token:
        conn.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
        conn.commit()
    # Los atributos deben coincidir con los del set_cookie para que el
    # navegador borre la cookie de verdad.
    response.delete_cookie(
        COOKIE_NOMBRE,
        httponly=True,
        samesite="lax",
        secure=_cookie_segura(request),
    )
    return {"detalle": "Sesión cerrada"}


# Reexport para usar como dependencia en los routers.
SesionActual = Depends(usuario_actual)
