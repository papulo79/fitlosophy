"""Tests del registro de actividad externa (docs/morning_state/especificacion_actividad_externa.md).

Deporte fuera del generador (BJJ, grappling, otra): varios registros por día,
carga orientativa en UA (duración × RPE) calculada al leer, edición, borrado
con 404 entre usuarios e inclusión en el historial y en el export. No alimenta
el motor ni `bjj_records`.
"""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from fitlosophy_api.app import create_app
from fitlosophy_api.db import conectar
from fitlosophy_api.usuarios import alta_usuario

USUARIO = "atleta"
PASSWORD = "secreto123456"


@pytest.fixture()
def app(tmp_path):
    aplicacion = create_app(tmp_path / "test.db")
    with conectar(aplicacion.state.db_path) as conn:
        aplicacion.state.user_id = alta_usuario(conn, USUARIO, PASSWORD)
    return aplicacion


@pytest.fixture(autouse=True)
def proxy_de_pruebas(monkeypatch):
    monkeypatch.setenv("FITLOSOPHY_PROXIES_CONFIABLES", "testclient")


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        r = c.post("/api/auth/login", json={"username": USUARIO, "password": PASSWORD})
        assert r.status_code == 200
        yield c


HOY = date.today().isoformat()
AYER = (date.today() - timedelta(days=1)).isoformat()

EJEMPLO = {  # el de los criterios de aceptación: BJJ · 60 min · RPE 7 · 5 combates → 420 UA
    "fecha": HOY,
    "tipo": "bjj",
    "duracion_minutos": 60,
    "rpe": 7,
    "combates": 5,
}


def test_registrar_y_ver_en_historial(client):
    r = client.post("/api/actividades", json=EJEMPLO)
    assert r.status_code == 201
    actividad_id = r.json()["id"]

    detalle = client.get(f"/api/historial/{HOY}").json()
    assert len(detalle["actividades"]) == 1
    a = detalle["actividades"][0]
    assert a["id"] == actividad_id
    assert a["tipo"] == "bjj"
    assert a["duracion_minutos"] == 60
    assert a["rpe"] == 7
    assert a["carga_ua"] == 420
    assert a["combates"] == 5

    lista = client.get("/api/historial?dias=3").json()["dias"]
    hoy = next(d for d in lista if d["fecha"] == HOY)
    assert "externa" in hoy["tipos"]
    assert hoy["actividades"][0]["rpe"] == 7


def test_varias_actividades_el_mismo_dia(client):
    client.post("/api/actividades", json=EJEMPLO)
    client.post(
        "/api/actividades",
        json={"fecha": HOY, "tipo": "grappling", "duracion_minutos": 45, "rpe": 5},
    )
    detalle = client.get(f"/api/historial/{HOY}").json()
    assert len(detalle["actividades"]) == 2


def test_otra_exige_nombre(client):
    sin_nombre = {"fecha": HOY, "tipo": "otra", "duracion_minutos": 30, "rpe": 4}
    assert client.post("/api/actividades", json=sin_nombre).status_code == 422
    con_nombre = {**sin_nombre, "nombre": "Natación"}
    r = client.post("/api/actividades", json=con_nombre)
    assert r.status_code == 201
    detalle = client.get(f"/api/historial/{HOY}").json()
    assert detalle["actividades"][0]["nombre"] == "Natación"


def test_validacion_de_obligatorios(client):
    assert client.post("/api/actividades", json={"tipo": "bjj", "duracion_minutos": 60, "rpe": 7}).status_code == 422
    assert client.post("/api/actividades", json={**EJEMPLO, "duracion_minutos": 0}).status_code == 422
    assert client.post("/api/actividades", json={**EJEMPLO, "rpe": 0}).status_code == 422
    assert client.post("/api/actividades", json={**EJEMPLO, "rpe": 11}).status_code == 422
    assert client.post("/api/actividades", json={**EJEMPLO, "combates": -1}).status_code == 422


def test_combates_vacio_no_es_cero(client):
    cuerpo = {k: v for k, v in EJEMPLO.items() if k != "combates"}
    client.post("/api/actividades", json=cuerpo)
    detalle = client.get(f"/api/historial/{HOY}").json()
    assert detalle["actividades"][0]["combates"] is None


def test_editar_actualiza_la_carga(client):
    actividad_id = client.post("/api/actividades", json=EJEMPLO).json()["id"]
    r = client.put(f"/api/actividades/{actividad_id}", json={**EJEMPLO, "duracion_minutos": 90, "rpe": 8})
    assert r.status_code == 200
    a = client.get(f"/api/historial/{HOY}").json()["actividades"][0]
    assert a["duracion_minutos"] == 90
    assert a["carga_ua"] == 720


def test_eliminar(client):
    actividad_id = client.post("/api/actividades", json=EJEMPLO).json()["id"]
    r = client.delete(f"/api/actividades/{actividad_id}")
    assert r.status_code == 200
    assert client.get(f"/api/historial/{HOY}").json()["actividades"] == []
    assert client.delete(f"/api/actividades/{actividad_id}").status_code == 404


def test_aislamiento_entre_usuarios(app, client):
    actividad_id = client.post("/api/actividades", json=EJEMPLO).json()["id"]
    with conectar(app.state.db_path) as conn:
        alta_usuario(conn, "otra", "password123456")
    with TestClient(app) as c2:
        r = c2.post("/api/auth/login", json={"username": "otra", "password": "password123456"})
        assert r.status_code == 200
        # 404, no 403: un 403 confirmaría que el identificador es de otra persona.
        assert c2.put(f"/api/actividades/{actividad_id}", json=EJEMPLO).status_code == 404
        assert c2.delete(f"/api/actividades/{actividad_id}").status_code == 404
        assert c2.get(f"/api/historial/{HOY}").json()["actividades"] == []


def test_export_incluye_actividades(client):
    client.post("/api/actividades", json=EJEMPLO)
    datos = client.get("/api/export").json()["datos"]
    assert len(datos["external_activities"]) == 1
    assert datos["external_activities"][0]["tipo"] == "bjj"


def test_sin_autenticacion(app):
    with TestClient(app) as c:
        assert c.post("/api/actividades", json=EJEMPLO).status_code == 401
        assert c.put("/api/actividades/1", json=EJEMPLO).status_code == 401
        assert c.delete("/api/actividades/1").status_code == 401


# --- Unificación: BJJ/grappling también alimenta el motor (bjj_records enlazado) ---------


def _bjj_enlazados(app):
    with conectar(app.state.db_path) as conn:
        return conn.execute(
            "SELECT * FROM bjj_records WHERE external_activity_id IS NOT NULL"
        ).fetchall()


def test_bjj_crea_registro_enlazado_para_el_motor(app, client):
    actividad_id = client.post("/api/actividades", json={**EJEMPLO, "fatiga_agarre": True}).json()["id"]
    enlazados = _bjj_enlazados(app)
    assert len(enlazados) == 1
    bjj = enlazados[0]
    assert bjj["external_activity_id"] == actividad_id
    assert bjj["clasificacion"] == "normal"  # RPE 7
    assert bjj["duracion_minutos"] == 60
    assert bjj["intensidad_percibida"] == 7
    assert bjj["fatiga_agarre"] == 1
    assert bjj["estimado"] == 0  # es un dato declarado, no una estimación


def test_clasificacion_desde_rpe(app, client):
    client.post("/api/actividades", json={**EJEMPLO, "rpe": 3})
    client.post("/api/actividades", json={**EJEMPLO, "tipo": "grappling", "rpe": 9})
    clases = sorted(b["clasificacion"] for b in _bjj_enlazados(app))
    assert clases == ["duro", "tecnico"]


def test_otra_no_alimenta_el_motor(app, client):
    client.post(
        "/api/actividades",
        json={"fecha": HOY, "tipo": "otra", "nombre": "Natación", "duracion_minutos": 30, "rpe": 4},
    )
    assert _bjj_enlazados(app) == []


def test_enlazado_aparece_una_sola_vez_en_el_historial(client):
    client.post("/api/actividades", json=EJEMPLO)
    detalle = client.get(f"/api/historial/{HOY}").json()
    assert detalle["bjj"] == []  # se muestra como actividad externa, no duplicado
    assert len(detalle["actividades"]) == 1
    lista = client.get("/api/historial?dias=1").json()["dias"]
    assert lista[0]["tipos"] == ["externa"]


def test_editar_sincroniza_el_enlazado(app, client):
    actividad_id = client.post("/api/actividades", json=EJEMPLO).json()["id"]
    # Cambiar el RPE recalcula la clasificación que ve el motor.
    client.put(f"/api/actividades/{actividad_id}", json={**EJEMPLO, "rpe": 9})
    assert _bjj_enlazados(app)[0]["clasificacion"] == "duro"
    # Cambiar a «otra» retira la actividad del motor.
    client.put(
        f"/api/actividades/{actividad_id}",
        json={**EJEMPLO, "tipo": "otra", "nombre": "Natación"},
    )
    assert _bjj_enlazados(app) == []


def test_eliminar_borra_el_enlazado(app, client):
    actividad_id = client.post("/api/actividades", json=EJEMPLO).json()["id"]
    assert len(_bjj_enlazados(app)) == 1
    client.delete(f"/api/actividades/{actividad_id}")
    assert _bjj_enlazados(app) == []


def test_bjj_manual_sin_enlace_sigue_apareciendo(client):
    # Los registros de BJJ anteriores a la unificación (sin actividad enlazada)
    # se siguen mostrando y corrigiendo como antes.
    client.post("/api/bjj", json={"clasificacion": "duro", "duracion_minutos": 90})
    detalle = client.get(f"/api/historial/{HOY}").json()
    assert len(detalle["bjj"]) == 1
    assert detalle["bjj"][0]["clasificacion"] == "duro"
