"""Persistencia SQLite del MVP (stdlib `sqlite3`, sin ORM).

Esquema simple y exportable. Toda fecha se guarda como ISO 8601 (local, naive)
y las estructuras compuestas como JSON.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS auth_sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS daily_states (
    id INTEGER PRIMARY KEY,
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
);
CREATE TABLE IF NOT EXISTS proposals (
    id INTEGER PRIMARY KEY,
    daily_state_id INTEGER NOT NULL REFERENCES daily_states(id),
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
);
CREATE TABLE IF NOT EXISTS training_sessions (
    id INTEGER PRIMARY KEY,
    proposal_id INTEGER REFERENCES proposals(id),
    fecha TEXT NOT NULL,
    familia TEXT,
    estado TEXT NOT NULL,              -- en_curso | finalizada | cerrada
    rpe_real INTEGER,
    created_at TEXT NOT NULL,
    finalizada_at TEXT
);
CREATE TABLE IF NOT EXISTS session_items (
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
);
CREATE TABLE IF NOT EXISTS session_closures (
    id INTEGER PRIMARY KEY,
    session_id INTEGER UNIQUE NOT NULL REFERENCES training_sessions(id),
    sensacion TEXT NOT NULL,           -- como_previsto | mas_duro | mas_suave
    molestias TEXT NOT NULL,           -- JSON lista de {zona, intensidad}
    dimensiones_congeladas TEXT NOT NULL DEFAULT '[]',  -- JSON
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bjj_records (
    id INTEGER PRIMARY KEY,
    fecha TEXT NOT NULL,
    clasificacion TEXT NOT NULL,       -- tecnico | normal | duro
    duracion_minutos INTEGER NOT NULL,
    fatiga_agarre INTEGER NOT NULL DEFAULT 0,
    intensidad_percibida INTEGER,
    notas TEXT,
    estimado INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    data TEXT NOT NULL,                -- JSON con la forma de data/perfil.yaml
    updated_at TEXT NOT NULL
);
"""


def conectar(db_path: str | Path) -> sqlite3.Connection:
    # check_same_thread=False: FastAPI ejecuta los endpoints en un pool de
    # hilos; el acceso se serializa con el lock de la aplicación (app personal
    # de un único usuario).
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def crear_esquema(conn: sqlite3.Connection) -> None:
    conn.executescript(ESQUEMA)
    conn.commit()


def cargar_json(valor: str | None, por_defecto):
    if valor is None:
        return por_defecto
    return json.loads(valor)


def volcar_json(valor) -> str:
    return json.dumps(valor, ensure_ascii=False)
