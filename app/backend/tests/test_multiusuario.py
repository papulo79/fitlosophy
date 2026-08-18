"""Aislamiento entre usuarios (docs/14, criterio 10) y migración del esquema.

Dos atletas comparten despliegue. Lo que se comprueba aquí es que no comparten
nada más: ni recursos accesibles por identificador, ni historial, ni carga
activa, ni flujo. La parte más cara de un fallo aquí no es la privacidad sino
la decisión: si el historial se mezclara, el motor propondría a todos sesiones
reducidas por entrenamientos que no han hecho.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from fitlosophy.load import compute_load
from fitlosophy_api.app import create_app
from fitlosophy_api.db import conectar, crear_esquema
from fitlosophy_api.history import construir_historial
from fitlosophy_api.usuarios import ErrorUsuario, alta_usuario, cambiar_password, listar_usuarios

PASSWORD_A = "contrasena-de-ana"
PASSWORD_B = "contrasena-de-bea"


@pytest.fixture()
def app(tmp_path):
    aplicacion = create_app(tmp_path / "multi.db")
    with conectar(aplicacion.state.db_path) as conn:
        aplicacion.state.id_ana = alta_usuario(conn, "ana", PASSWORD_A)
        aplicacion.state.id_bea = alta_usuario(conn, "bea", PASSWORD_B)
    return aplicacion


@pytest.fixture(autouse=True)
def proxy_de_pruebas(monkeypatch):
    monkeypatch.setenv("FITLOSOPHY_PROXIES_CONFIABLES", "testclient")


def _entrar(app, username, password):
    c = TestClient(app)
    r = c.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return c


@pytest.fixture()
def ana(app):
    with _entrar(app, "ana", PASSWORD_A) as c:
        yield c


@pytest.fixture()
def bea(app):
    with _entrar(app, "bea", PASSWORD_B) as c:
        yield c


def _propuesta(client, **estado):
    base = {"recuperacion": "verde", "dolor": 0, "bjj_disponible": "no"}
    base.update(estado)
    r = client.post("/api/estado-diario", json=base)
    assert r.status_code == 201, r.text
    return r.json()["propuesta"]


def _sesion_entrenada(client, rpe=7):
    """Propuesta → sesión → finalizada. Devuelve la sesión finalizada."""
    propuesta = _propuesta(client)
    r = client.post("/api/sesiones", json={"proposal_id": propuesta["id"]})
    assert r.status_code == 201, r.text
    sesion = r.json()["sesion"]
    r = client.post(f"/api/sesiones/{sesion['id']}/finalizar", json={"rpe_real": rpe})
    assert r.status_code == 200, r.text
    return r.json()["sesion"]


# --- Ningún identificador ajeno es accesible ------------------------------------------


def test_todos_los_recursos_ajenos_responden_404(ana, bea):
    """Recorre los endpoints con id: con la sesión de Bea, nada de Ana existe.

    404 y no 403: un 403 confirmaría que ese identificador es de alguien.
    """
    propuesta = _propuesta(ana)
    r = ana.post("/api/sesiones", json={"proposal_id": propuesta["id"]})
    sesion = r.json()["sesion"]
    item = sesion["items"][0]
    r = ana.post("/api/bjj", json={"clasificacion": "normal", "duracion_minutos": 60})
    bjj_id = r.json()["id"]

    s, i = sesion["id"], item["id"]
    peticiones = [
        ("post", f"/api/propuestas/{propuesta['id']}/sustituir", {"item_indice": 0, "exercise_id": "kb-swing-two-hand"}),
        ("get", f"/api/sesiones/{s}", None),
        ("post", f"/api/sesiones/{s}/cancelar", None),
        ("patch", f"/api/sesiones/{s}/items/{i}", {"estado": "completado"}),
        ("put", f"/api/sesiones/{s}/items/{i}", {"estado": "completado"}),
        ("post", f"/api/sesiones/{s}/finalizar", {"rpe_real": 7}),
        ("post", f"/api/sesiones/{s}/cierre", {"sensacion": "como_previsto", "molestias": []}),
        ("put", f"/api/sesiones/{s}", {"rpe_real": 6}),
        ("put", f"/api/sesiones/{s}/cierre", {"sensacion": "mas_duro"}),
        ("put", f"/api/bjj/{bjj_id}", {"clasificacion": "duro"}),
    ]
    for metodo, url, cuerpo in peticiones:
        r = getattr(bea, metodo)(url, json=cuerpo) if cuerpo is not None else getattr(bea, metodo)(url)
        assert r.status_code == 404, f"{metodo.upper()} {url} devolvió {r.status_code}"

    # Y aceptar la propuesta de otra tampoco: sería entrenar su sesión.
    r = bea.post("/api/sesiones", json={"proposal_id": propuesta["id"]})
    assert r.status_code == 404


def test_una_correccion_ajena_no_modifica_nada(ana, bea):
    """El 404 no es solo el código: la corrección rechazada no deja rastro."""
    sesion = _sesion_entrenada(ana)
    assert bea.put(f"/api/sesiones/{sesion['id']}", json={"rpe_real": 2}).status_code == 404
    assert ana.get(f"/api/sesiones/{sesion['id']}").json()["sesion"]["rpe_real"] == 7


# --- Historial y carga activa ----------------------------------------------------------


def test_el_historial_del_motor_solo_ve_lo_propio(app, ana, bea):
    """El fallo caro: sin filtrar, la carga de Ana incluiría la de Bea y el
    motor propondría a las dos sesiones reducidas por trabajo ajeno."""
    _sesion_entrenada(ana)
    ana.post("/api/bjj", json={"clasificacion": "duro", "duracion_minutos": 90})

    with conectar(app.state.db_path) as conn:
        catalog = app.state.catalog
        eventos_ana = construir_historial(conn, catalog, app.state.id_ana)
        eventos_bea = construir_historial(conn, catalog, app.state.id_bea)
        assert eventos_ana, "Ana entrenó y tiene BJJ"
        assert eventos_bea == [], "Bea no ha hecho nada"
        carga_bea = compute_load(eventos_bea, catalog, datetime.now())
        assert all(p == 0 for p in carga_bea.puntos.values())
        carga_ana = compute_load(eventos_ana, catalog, datetime.now())
        assert any(p > 0 for p in carga_ana.puntos.values())

    # Y desde la API: la propuesta de Bea nace con la carga a cero.
    assert all(p == 0 for p in _propuesta(bea)["carga"]["puntos"].values())


def test_el_historial_por_dias_no_mezcla(ana, bea):
    _sesion_entrenada(ana)
    ana.post("/api/bjj", json={"clasificacion": "normal", "duracion_minutos": 60})
    hoy = datetime.now().date().isoformat()

    dia_bea = next(d for d in bea.get("/api/historial").json()["dias"] if d["fecha"] == hoy)
    assert dia_bea["sesiones"] == [] and dia_bea["bjj"] == []
    assert dia_bea["tipos"] == ["sin_registro"]

    detalle_bea = bea.get(f"/api/historial/{hoy}").json()
    assert detalle_bea["sesiones"] == []
    assert detalle_bea["bjj"] == []
    assert detalle_bea["estados_diarios"] == []

    dia_ana = next(d for d in ana.get("/api/historial").json()["dias"] if d["fecha"] == hoy)
    assert "fisica" in dia_ana["tipos"] and "bjj" in dia_ana["tipos"]


def test_la_exportacion_solo_lleva_lo_propio(ana, bea):
    _sesion_entrenada(ana)
    ana.post("/api/bjj", json={"clasificacion": "normal", "duracion_minutos": 60})
    _propuesta(bea)

    datos = bea.get("/api/export").json()["datos"]
    assert datos["bjj_records"] == []
    assert datos["training_sessions"] == []
    assert datos["session_items"] == []
    assert len(datos["daily_states"]) == 1
    assert len(datos["profiles"]) == 1
    assert all(f["user_id"] == 2 for f in datos["daily_states"])


# --- El flujo de uno no interfiere con el del otro ---------------------------------------


def test_dos_pueden_entrenar_a_la_vez(ana, bea):
    """El invariante «una sola sesión activa» es de cada usuario. Con el filtro
    global, la primera persona en empezar bloqueaba a todas las demás."""
    propuesta_ana = _propuesta(ana)
    assert ana.post("/api/sesiones", json={"proposal_id": propuesta_ana["id"]}).status_code == 201

    propuesta_bea = _propuesta(bea)
    r = bea.post("/api/sesiones", json={"proposal_id": propuesta_bea["id"]})
    assert r.status_code == 201, "que Ana esté entrenando no puede frenar a Bea"

    # Cada una recupera la suya al reabrir la aplicación.
    hoy_ana = ana.get("/api/hoy").json()
    hoy_bea = bea.get("/api/hoy").json()
    assert hoy_ana["sesion_activa"]["id"] != hoy_bea["sesion_activa"]["id"]
    assert hoy_ana["sesion_activa"]["id"] == r.json()["sesion"]["id"] - 1


def test_redeclarar_el_estado_no_descarta_la_propuesta_ajena(ana, bea):
    propuesta_bea = _propuesta(bea)
    _propuesta(ana)  # Ana declara el suyo después
    _propuesta(ana)  # y lo vuelve a declarar: descarta el suyo anterior

    vigente = bea.get("/api/hoy").json()["propuesta_vigente"]
    assert vigente is not None and vigente["id"] == propuesta_bea["id"]
    assert vigente["estado"] == "vigente"


def test_hoy_no_arrastra_el_cierre_pendiente_de_otro(ana, bea):
    """Una sesión finalizada sin cerrar llevaba a la pantalla de cierre. Sin
    filtrar, Bea acabaría cerrando la sesión de Ana."""
    _sesion_entrenada(ana)
    assert ana.get("/api/hoy").json()["sesion_pendiente_cierre"] is not None
    assert bea.get("/api/hoy").json()["sesion_pendiente_cierre"] is None


# --- Perfil ---------------------------------------------------------------------------


def test_cada_usuario_tiene_su_perfil(ana, bea):
    perfil_ana = ana.get("/api/perfil").json()
    perfil_bea = bea.get("/api/perfil").json()
    # Ambos nacen de la plantilla: mismo material, nada personal.
    assert perfil_ana["material"] == perfil_bea["material"]
    assert perfil_ana["data"]["persona"]["peso_kg"] is None

    datos = dict(perfil_ana["data"])
    datos["persona"] = {**datos["persona"], "peso_kg": 68}
    assert ana.put("/api/perfil", json={"data": datos}).status_code == 200

    assert ana.get("/api/perfil").json()["data"]["persona"]["peso_kg"] == 68
    assert bea.get("/api/perfil").json()["data"]["persona"]["peso_kg"] is None


def test_el_perfil_ajusta_solo_las_propias_kettlebells(ana, bea):
    """`pesos_disponibles` sale del perfil del dueño de la sesión."""
    datos = ana.get("/api/perfil").json()["data"]
    datos["material"] = {**datos["material"], "kettlebells_kg": [24]}
    ana.put("/api/perfil", json={"data": datos})

    propuesta = _propuesta(ana)
    sesion_ana = ana.post("/api/sesiones", json={"proposal_id": propuesta["id"]}).json()["sesion"]
    assert sesion_ana["pesos_disponibles"] == [24]

    propuesta_bea = _propuesta(bea)
    sesion_bea = bea.post("/api/sesiones", json={"proposal_id": propuesta_bea["id"]}).json()["sesion"]
    assert sesion_bea["pesos_disponibles"] == [8, 12, 16]


# --- Alta y contraseñas -----------------------------------------------------------------


def test_el_alta_valida_y_no_admite_duplicados(app):
    with conectar(app.state.db_path) as conn:
        with pytest.raises(ErrorUsuario, match="ya existe"):
            alta_usuario(conn, "ana", "otra-contrasena-larga")
        with pytest.raises(ErrorUsuario, match="12 caracteres"):
            alta_usuario(conn, "cris", "corta")
        with pytest.raises(ErrorUsuario, match="minúscula"):
            alta_usuario(conn, "Cris Con Espacios", "contrasena-valida-1")
        assert [u["username"] for u in listar_usuarios(conn)] == ["ana", "bea"]


def test_un_correo_vale_como_nombre_de_usuario(app):
    """El primer usuario del despliegue real se dio de alta con su correo. Un
    patrón que lo rechazara le dejaría sin poder cambiar la contraseña."""
    with conectar(app.state.db_path) as conn:
        alta_usuario(conn, "alguien@ejemplo.com", "contrasena-por-correo")
        assert cambiar_password(conn, "alguien@ejemplo.com", "otra-contrasena-larga") == 0

    with _entrar(app, "alguien@ejemplo.com", "otra-contrasena-larga") as c:
        assert c.get("/api/auth/me").json()["username"] == "alguien@ejemplo.com"


def test_cambiar_la_contrasena_solo_cierra_las_sesiones_de_ese_usuario(app, ana, bea):
    assert ana.get("/api/auth/me").status_code == 200
    with conectar(app.state.db_path) as conn:
        assert cambiar_password(conn, "ana", "contrasena-nueva-de-ana") == 1

    assert ana.get("/api/auth/me").status_code == 401, "la cookie de Ana ya no vale"
    assert bea.get("/api/auth/me").status_code == 200, "Bea sigue dentro"

    with _entrar(app, "ana", "contrasena-nueva-de-ana") as c:
        assert c.get("/api/auth/me").json()["username"] == "ana"


def test_el_freno_por_usuario_no_bloquea_a_los_demas(app, monkeypatch):
    """Fallar contra la cuenta de Ana desde muchas IPs la frena a ella; Bea
    entra sin enterarse."""
    monkeypatch.setenv("FITLOSOPHY_LOGIN_MAX_USUARIO", "4")
    with TestClient(app) as c:
        for i in range(4):
            r = c.post(
                "/api/auth/login",
                json={"username": "ana", "password": "incorrecta"},
                headers={"CF-Connecting-IP": f"198.51.100.{i}"},
            )
            assert r.status_code == 401

        # IP nueva y limpia: el límite por IP no la vería; el de usuario sí.
        r = c.post(
            "/api/auth/login",
            json={"username": "ana", "password": PASSWORD_A},
            headers={"CF-Connecting-IP": "198.51.100.200"},
        )
        assert r.status_code == 429
        assert "este usuario" in r.json()["detail"]

        r = c.post(
            "/api/auth/login",
            json={"username": "bea", "password": PASSWORD_B},
            headers={"CF-Connecting-IP": "198.51.100.201"},
        )
        assert r.status_code == 200


# --- Migración desde el esquema de un solo usuario ----------------------------------------

# Esquema tal y como estaba antes del multiusuario, con lo justo para que la
# migración tenga algo que mover. Va literal a propósito: si se generase desde
# `db.TABLAS` dejaría de ser una prueba de la migración.
ESQUEMA_ANTIGUO = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
    salt TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE daily_states (
    id INTEGER PRIMARY KEY, fecha TEXT NOT NULL, recuperacion TEXT NOT NULL, dolor INTEGER NOT NULL,
    zona_dolor TEXT, bjj_disponible TEXT NOT NULL, tipo_bjj TEXT, limitacion TEXT, sueno TEXT,
    tiempo_disponible INTEGER, preferencia TEXT, circunstancias TEXT, material_disponible TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE proposals (
    id INTEGER PRIMARY KEY, daily_state_id INTEGER NOT NULL REFERENCES daily_states(id),
    estado TEXT NOT NULL DEFAULT 'vigente', fecha TEXT NOT NULL, familia TEXT NOT NULL,
    reducida INTEGER NOT NULL DEFAULT 0, techo TEXT, bjj_efectivo TEXT, rpe_previsto TEXT,
    presupuestos TEXT NOT NULL, patrones_prioritarios TEXT NOT NULL, patrones_restringidos TEXT NOT NULL,
    patrones_dosificados TEXT NOT NULL, d3 INTEGER NOT NULL DEFAULT 0, d4 INTEGER NOT NULL DEFAULT 0,
    d5 INTEGER NOT NULL DEFAULT 0, reglas TEXT NOT NULL, incertidumbres TEXT NOT NULL,
    explicacion TEXT NOT NULL, carga TEXT NOT NULL, items TEXT NOT NULL, notas TEXT NOT NULL,
    duracion_estimada_min INTEGER, valida INTEGER NOT NULL DEFAULT 1,
    violaciones TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL
);
CREATE TABLE training_sessions (
    id INTEGER PRIMARY KEY, proposal_id INTEGER REFERENCES proposals(id), fecha TEXT NOT NULL,
    familia TEXT, estado TEXT NOT NULL, rpe_real INTEGER, created_at TEXT NOT NULL, finalizada_at TEXT
);
CREATE TABLE session_items (
    id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL REFERENCES training_sessions(id),
    bloque TEXT NOT NULL, exercise_id TEXT NOT NULL, dosis TEXT, puntos_previstos TEXT NOT NULL,
    justificacion TEXT, estado TEXT NOT NULL DEFAULT 'pendiente', exercise_id_real TEXT,
    series_real INTEGER, repeticiones_real INTEGER, segundos_real REAL, minutos_real REAL,
    carga_kg_real REAL, motivo TEXT, puntos_reales TEXT
);
CREATE TABLE bjj_records (
    id INTEGER PRIMARY KEY, fecha TEXT NOT NULL, clasificacion TEXT NOT NULL,
    duracion_minutos INTEGER NOT NULL, fatiga_agarre INTEGER NOT NULL DEFAULT 0,
    intensidad_percibida INTEGER, notas TEXT, estimado INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE profile (
    id INTEGER PRIMARY KEY CHECK (id = 1), data TEXT NOT NULL, updated_at TEXT NOT NULL
);
INSERT INTO users (id, username, password_hash, salt, created_at)
    VALUES (1, 'antiguo', 'x', 'y', '2026-08-01T10:00:00');
INSERT INTO daily_states (id, fecha, recuperacion, dolor, bjj_disponible, created_at)
    VALUES (7, '2026-08-01T16:00:00', 'verde', 0, 'no', '2026-08-01T16:00:00');
INSERT INTO proposals (id, daily_state_id, fecha, familia, presupuestos, patrones_prioritarios,
    patrones_restringidos, patrones_dosificados, reglas, incertidumbres, explicacion, carga, items,
    notas, created_at)
    VALUES (3, 7, '2026-08-01T16:00:00', 'B', '{}', '[]', '{}', '[]', '[]', '[]', 'texto',
            '{}', '[]', '[]', '2026-08-01T16:00:00');
INSERT INTO training_sessions (id, proposal_id, fecha, familia, estado, rpe_real, created_at)
    VALUES (5, 3, '2026-08-01T17:00:00', 'B', 'cerrada', 8, '2026-08-01T17:00:00');
INSERT INTO session_items (id, session_id, bloque, exercise_id, puntos_previstos)
    VALUES (11, 5, 'B1', 'kb-swing-two-hand', '{"bisagra": 3}');
INSERT INTO bjj_records (id, fecha, clasificacion, duracion_minutos, created_at)
    VALUES (2, '2026-08-02T20:00:00', 'normal', 90, '2026-08-02T20:00:00');
INSERT INTO profile (id, data, updated_at) VALUES (1, '{"material": {}}', '2026-08-01T10:00:00');
"""


@pytest.fixture()
def bd_antigua(tmp_path):
    ruta = tmp_path / "antigua.db"
    conn = conectar(ruta)
    conn.executescript(ESQUEMA_ANTIGUO)
    conn.commit()
    conn.close()
    return ruta


def test_la_migracion_asigna_los_datos_al_usuario_existente(bd_antigua):
    with conectar(bd_antigua) as conn:
        crear_esquema(conn)

        for tabla, id_esperado in (("daily_states", 7), ("proposals", 3), ("training_sessions", 5), ("bjj_records", 2)):
            filas = conn.execute(f"SELECT * FROM {tabla}").fetchall()
            assert len(filas) == 1, tabla
            assert filas[0]["user_id"] == 1, tabla
            # Los identificadores se conservan: las referencias apuntan a ellos.
            assert filas[0]["id"] == id_esperado, tabla

        item = conn.execute("SELECT * FROM session_items").fetchone()
        assert item["session_id"] == 5, "el ítem sigue colgando de su sesión"

        perfil = conn.execute("SELECT * FROM profiles").fetchall()
        assert len(perfil) == 1 and perfil[0]["user_id"] == 1
        assert not conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'profile'"
        ).fetchall(), "la tabla de perfil único se retira"

        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_la_migracion_es_idempotente(bd_antigua):
    with conectar(bd_antigua) as conn:
        crear_esquema(conn)
        crear_esquema(conn)
        crear_esquema(conn)
        assert conn.execute("SELECT COUNT(*) FROM daily_states").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0] == 1


def test_la_migracion_se_niega_a_inventar_un_dueno(tmp_path):
    """Datos sin ningún usuario: no hay a quién asignárselos y parar es lo
    correcto. Asignarlos al primero que se cree después sería peor."""
    ruta = tmp_path / "sin-usuario.db"
    with conectar(ruta) as conn:
        conn.executescript(ESQUEMA_ANTIGUO)
        conn.execute("DELETE FROM users")
        conn.commit()
        with pytest.raises(RuntimeError, match="crear_usuario"):
            crear_esquema(conn)


def test_una_base_de_datos_nueva_no_necesita_migracion(tmp_path):
    """Fresca y migrada tienen que quedar con el mismo esquema: si divergen,
    lo que se prueba aquí deja de valer para el despliegue real."""
    nueva = tmp_path / "nueva.db"
    with conectar(nueva) as conn:
        crear_esquema(conn)
        esquema_nuevo = _esquema(conn)

    ruta_antigua = tmp_path / "vieja.db"
    with conectar(ruta_antigua) as conn:
        conn.executescript(ESQUEMA_ANTIGUO)
        conn.commit()
        crear_esquema(conn)
        esquema_migrado = _esquema(conn)

    assert esquema_migrado == esquema_nuevo


def _esquema(conn) -> dict[str, list[tuple]]:
    """Columnas de cada tabla: nombre, tipo, not-null y valor por defecto."""
    tablas = [
        f["name"]
        for f in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    return {
        t: [(c["name"], c["type"], c["notnull"], c["dflt_value"]) for c in conn.execute(f"PRAGMA table_info({t})")]
        for t in tablas
    }
