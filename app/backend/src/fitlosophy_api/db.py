"""Persistencia SQLite del MVP (stdlib `sqlite3`, sin ORM).

Esquema simple y exportable. Toda fecha se guarda como ISO 8601 (local, naive)
y las estructuras compuestas como JSON.

**Todo dato es de un usuario** (docs/14: acceso y privacidad). Las cuatro tablas
raíz —`daily_states`, `proposals`, `training_sessions`, `bjj_records`— llevan
`user_id`, y `profiles` tiene una fila por usuario. `session_items` y
`session_closures` no lo repiten: cuelgan de `training_sessions` y se filtran
por su sesión.

Las definiciones viven en `TABLAS` (una por clave) en lugar de en un bloque de
SQL suelto, porque la migración a multiusuario necesita reconstruir tablas y
debe hacerlo con la misma definición que usa una base de datos nueva. Con dos
copias del `CREATE TABLE` acabarían divergiendo.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi import Request

# Espera máxima a que se libere la base de datos antes de dar error. Con tres
# personas la contención es rara y brevísima; el margen es para no fallar si
# coincide con una escritura larga.
SEGUNDOS_ESPERA = 5.0

# `{nombre}` lo sustituye `_sql_tabla`: `crear_esquema` pone el nombre
# definitivo y la migración el temporal (`<tabla>_nueva`) al reconstruir.
TABLAS: dict[str, str] = {
    "users": """
CREATE TABLE IF NOT EXISTS {nombre} (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TEXT NOT NULL
)""",
    "auth_sessions": """
CREATE TABLE IF NOT EXISTS {nombre} (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
)""",
    "daily_states": """
CREATE TABLE IF NOT EXISTS {nombre} (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    fecha TEXT NOT NULL,
    recuperacion TEXT NOT NULL,
    dolor INTEGER NOT NULL,
    zona_dolor TEXT,
    bjj_disponible TEXT NOT NULL,
    tipo_bjj TEXT,
    limitacion TEXT,
    sueno TEXT,
    tiempo_disponible INTEGER,
    preferencia TEXT,
    circunstancias TEXT,
    material_disponible TEXT,          -- JSON lista o NULL (= todo el inventario)
    created_at TEXT NOT NULL
)""",
    "proposals": """
CREATE TABLE IF NOT EXISTS {nombre} (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    daily_state_id INTEGER NOT NULL REFERENCES daily_states(id),
    estado TEXT NOT NULL DEFAULT 'vigente',   -- vigente | aceptada | descartada
    fecha TEXT NOT NULL,
    familia TEXT NOT NULL,
    reducida INTEGER NOT NULL DEFAULT 0,
    techo TEXT,
    bjj_efectivo TEXT,
    rpe_previsto TEXT,
    presupuestos TEXT NOT NULL,        -- JSON
    patrones_prioritarios TEXT NOT NULL,
    patrones_restringidos TEXT NOT NULL,
    patrones_dosificados TEXT NOT NULL,
    d3 INTEGER NOT NULL DEFAULT 0,
    d4 INTEGER NOT NULL DEFAULT 0,
    d5 INTEGER NOT NULL DEFAULT 0,
    reglas TEXT NOT NULL,              -- JSON
    incertidumbres TEXT NOT NULL,      -- JSON
    explicacion TEXT NOT NULL,
    carga TEXT NOT NULL,               -- JSON LoadVector
    items TEXT NOT NULL,               -- JSON lista de ítems de la sesión
    notas TEXT NOT NULL,               -- JSON
    duracion_estimada_min INTEGER,
    valida INTEGER NOT NULL DEFAULT 1,
    violaciones TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
)""",
    "training_sessions": """
CREATE TABLE IF NOT EXISTS {nombre} (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    proposal_id INTEGER REFERENCES proposals(id),
    fecha TEXT NOT NULL,
    familia TEXT,
    estado TEXT NOT NULL,              -- en_curso | finalizada | cerrada | cancelada
    rpe_real INTEGER,
    created_at TEXT NOT NULL,
    finalizada_at TEXT
)""",
    # Sin `user_id`: el dueño es el de su `training_sessions`. Repetirlo abriría
    # la puerta a que las dos columnas discrepen.
    "session_items": """
CREATE TABLE IF NOT EXISTS {nombre} (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES training_sessions(id),
    bloque TEXT NOT NULL,
    exercise_id TEXT NOT NULL,
    dosis TEXT,
    puntos_previstos TEXT NOT NULL,    -- JSON
    justificacion TEXT,
    estado TEXT NOT NULL DEFAULT 'pendiente',  -- pendiente|completado|modificado|sustituido|no_realizado
    exercise_id_real TEXT,
    series_real INTEGER,
    repeticiones_real INTEGER,
    segundos_real REAL,
    minutos_real REAL,
    carga_kg_real REAL,
    motivo TEXT,
    puntos_reales TEXT                 -- JSON; NULL hasta finalizar
)""",
    "session_closures": """
CREATE TABLE IF NOT EXISTS {nombre} (
    id INTEGER PRIMARY KEY,
    session_id INTEGER UNIQUE NOT NULL REFERENCES training_sessions(id),
    sensacion TEXT NOT NULL,           -- como_previsto | mas_duro | mas_suave
    molestias TEXT NOT NULL,           -- JSON lista de {zona, intensidad}
    dimensiones_congeladas TEXT NOT NULL DEFAULT '[]',  -- JSON
    created_at TEXT NOT NULL
)""",
    "bjj_records": """
CREATE TABLE IF NOT EXISTS {nombre} (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    fecha TEXT NOT NULL,
    clasificacion TEXT NOT NULL,       -- tecnico | normal | duro
    duracion_minutos INTEGER NOT NULL,
    fatiga_agarre INTEGER NOT NULL DEFAULT 0,
    intensidad_percibida INTEGER,
    notas TEXT,
    estimado INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
)""",
    # Un perfil por usuario (antes era una fila única con CHECK (id = 1)).
    "profiles": """
CREATE TABLE IF NOT EXISTS {nombre} (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    data TEXT NOT NULL,                -- JSON con la forma de data/perfil.yaml
    updated_at TEXT NOT NULL
)""",
    # Solo intentos de login FALLIDOS: alimentan el freno de fuerza bruta de
    # auth.py. Un login correcto borra los de esa IP y los de ese usuario; los
    # antiguos se purgan.
    "login_failures": """
CREATE TABLE IF NOT EXISTS {nombre} (
    id INTEGER PRIMARY KEY,
    ip TEXT NOT NULL,
    username TEXT,                     -- el declarado en el intento (puede no existir)
    ts TEXT NOT NULL
)""",
}

# Se crean después de migrar: en una base de datos antigua las columnas
# `user_id` todavía no existen cuando se aplica el esquema.
INDICES = """
CREATE INDEX IF NOT EXISTS idx_login_failures_ts ON login_failures(ts);
CREATE INDEX IF NOT EXISTS idx_login_failures_ip_ts ON login_failures(ip, ts);
CREATE INDEX IF NOT EXISTS idx_login_failures_user_ts ON login_failures(username, ts);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_states_user_fecha ON daily_states(user_id, fecha);
CREATE INDEX IF NOT EXISTS idx_proposals_user_fecha ON proposals(user_id, fecha);
CREATE INDEX IF NOT EXISTS idx_training_sessions_user_fecha ON training_sessions(user_id, fecha);
CREATE INDEX IF NOT EXISTS idx_bjj_records_user_fecha ON bjj_records(user_id, fecha);
CREATE INDEX IF NOT EXISTS idx_session_items_session ON session_items(session_id);
"""

# Tablas raíz que ganaron `user_id` al pasar a multiusuario.
TABLAS_CON_USUARIO = ("daily_states", "proposals", "training_sessions", "bjj_records")


def _sql_tabla(tabla: str, nombre: str) -> str:
    """Definición de `tabla` con el nombre `nombre`.

    Sustitución literal en vez de `str.format`: los comentarios del esquema
    llevan llaves y `format` las interpretaría como campos.
    """
    return TABLAS[tabla].replace("{nombre}", nombre)


def conectar(db_path: str | Path) -> sqlite3.Connection:
    # check_same_thread=False: FastAPI ejecuta los endpoints en un pool de
    # hilos y la conexión puede crearse en uno y usarse en otro.
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=SEGUNDOS_ESPERA)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # Con WAL solo se serializan los escritores; mientras uno escribe, los
    # demás siguen leyendo. `busy_timeout` hace que un escritor simultáneo
    # espere su turno en lugar de fallar con «database is locked».
    conn.execute(f"PRAGMA busy_timeout = {int(SEGUNDOS_ESPERA * 1000)}")
    return conn


def db_conn(request: Request):
    """Dependencia FastAPI: una conexión propia por petición.

    Antes había una única conexión compartida protegida por un lock global que
    se mantenía tomado durante toda la petición, de modo que el servidor
    atendía a una persona cada vez —y declarar el estado diario reconstruye el
    historial y ejecuta motor y generador—. Con varios atletas entrenando a la
    vez eso se notaba. Además, una conexión por petición da a cada una su
    propia transacción: un fallo a mitad ya no puede confirmar el trabajo a
    medias de otra.

    FastAPI cachea la dependencia dentro de la misma petición, así que el
    endpoint y `usuario_actual` comparten conexión.
    """
    conn = conectar(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()


def _columnas(conn: sqlite3.Connection, tabla: str) -> list[str]:
    return [c["name"] for c in conn.execute(f"PRAGMA table_info({tabla})")]


def _existe(conn: sqlite3.Connection, tabla: str) -> bool:
    fila = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (tabla,)
    ).fetchone()
    return fila is not None


def _migrar_estado_propuestas(conn: sqlite3.Connection) -> None:
    """Migración previa a multiusuario: columna `estado` en `proposals`.

    Se mantiene porque una base de datos anterior a ella todavía puede existir,
    y la reconstrucción posterior copia las columnas por nombre: `estado` tiene
    que estar ahí antes.
    """
    columnas = _columnas(conn, "proposals")
    if not columnas or "estado" in columnas:
        return
    conn.execute("ALTER TABLE proposals ADD COLUMN estado TEXT NOT NULL DEFAULT 'vigente'")
    # Las propuestas que ya tienen sesión estaban aceptadas de hecho.
    conn.execute(
        "UPDATE proposals SET estado = 'aceptada' "
        "WHERE id IN (SELECT proposal_id FROM training_sessions WHERE proposal_id IS NOT NULL)"
    )
    # Del resto solo sigue vigente la última de cada día: es el invariante
    # que la aplicación mantiene desde ahora (docs/14).
    conn.execute(
        "UPDATE proposals SET estado = 'descartada' WHERE estado = 'vigente' AND id NOT IN ("
        "  SELECT MAX(id) FROM proposals WHERE estado = 'vigente' GROUP BY date(fecha)"
        ")"
    )
    conn.commit()


def _reconstruir_con_usuario(conn: sqlite3.Connection, tabla: str, propietario: int | None) -> None:
    """Añade `user_id` a una tabla existente reconstruyéndola.

    SQLite no permite añadir con `ALTER TABLE` una columna que sea a la vez
    `NOT NULL` y `REFERENCES`: una columna nueva con clave foránea tiene que
    admitir NULL. Añadirla anulable dejaría el esquema de esta base de datos
    distinto para siempre del de una recién creada, así que se sigue el
    procedimiento de reconstrucción: tabla nueva con la definición definitiva,
    copia conservando los identificadores, borrado y renombrado.
    """
    antiguas = _columnas(conn, tabla)
    if "user_id" in antiguas:
        return  # ya migrada
    if propietario is None and conn.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]:
        raise RuntimeError(
            f"La tabla '{tabla}' tiene datos y no hay ningún usuario al que asignárselos. "
            "Crea el usuario con scripts/crear_usuario.py antes de migrar."
        )
    lista = ", ".join(antiguas)
    conn.executescript(
        f"""
        DROP TABLE IF EXISTS {tabla}_nueva;
        {_sql_tabla(tabla, f"{tabla}_nueva")};
        INSERT INTO {tabla}_nueva (user_id, {lista})
            SELECT {propietario if propietario is not None else "NULL"}, {lista} FROM {tabla};
        DROP TABLE {tabla};
        ALTER TABLE {tabla}_nueva RENAME TO {tabla};
        """
    )


def _migrar_perfil(conn: sqlite3.Connection, propietario: int | None) -> None:
    """`profile` (fila única con CHECK (id = 1)) → `profiles` (una por usuario)."""
    if not _existe(conn, "profile"):
        return
    filas = conn.execute("SELECT data, updated_at FROM profile").fetchall()
    if filas and propietario is None:
        raise RuntimeError(
            "Hay un perfil guardado y ningún usuario al que asignárselo. "
            "Crea el usuario con scripts/crear_usuario.py antes de migrar."
        )
    for fila in filas:
        conn.execute(
            "INSERT OR IGNORE INTO profiles (user_id, data, updated_at) VALUES (?, ?, ?)",
            (propietario, fila["data"], fila["updated_at"]),
        )
    conn.execute("DROP TABLE profile")


def _migrar_multiusuario(conn: sqlite3.Connection) -> None:
    """Asigna a un dueño los datos que se crearon cuando la aplicación era de
    un solo usuario (docs/14).

    Todo lo existente pasa al primer usuario de la tabla `users`, que es el
    único que había. Es idempotente: en una base de datos ya migrada —o recién
    creada— no hace nada.
    """
    pendientes = [t for t in TABLAS_CON_USUARIO if _existe(conn, t) and "user_id" not in _columnas(conn, t)]
    if not pendientes and not _existe(conn, "profile"):
        return

    fila = conn.execute("SELECT MIN(id) AS id FROM users").fetchone()
    propietario = fila["id"] if fila else None

    # `foreign_keys` no admite cambios dentro de una transacción, y durante la
    # reconstrucción hay tablas que apuntan a otra que se está borrando.
    conn.commit()
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        for tabla in pendientes:
            _reconstruir_con_usuario(conn, tabla, propietario)
        _migrar_perfil(conn, propietario)
        conn.commit()
        rotas = conn.execute("PRAGMA foreign_key_check").fetchall()
        if rotas:
            raise RuntimeError(
                f"La migración a multiusuario dejó referencias rotas: {[tuple(r) for r in rotas]}"
            )
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def crear_esquema(conn: sqlite3.Connection) -> None:
    # WAL queda grabado en el fichero: basta con pedirlo una vez.
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(";\n".join(_sql_tabla(nombre, nombre) for nombre in TABLAS))
    conn.commit()
    _migrar_estado_propuestas(conn)
    _migrar_multiusuario(conn)
    conn.executescript(INDICES)
    conn.commit()


def cargar_json(valor: str | None, por_defecto):
    if valor is None:
        return por_defecto
    return json.loads(valor)


def volcar_json(valor) -> str:
    return json.dumps(valor, ensure_ascii=False)
