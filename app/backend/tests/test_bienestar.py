"""Tests del registro matutino de bienestar (docs/morning_state).

Un registro por usuario y fecha, indicadores opcionales (registros parciales),
edición de días anteriores y días sin registro distinguibles de puntuaciones
bajas. Es informativo: no toca `daily_states` ni la planificación.
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

COMPLETO = {
    "calidad_sueno": 4,
    "recuperacion_fisica": 3,
    "molestias_fisicas": 5,
    "zonas_molestias": ["lumbar", "rodillas"],
    "energia_fisica": 2,
    "claridad_mental": 4,
    "estres_previsto": 5,
    "observaciones": "Dormí mal por el calor",
}


def test_guardar_y_consultar(client):
    r = client.put(f"/api/bienestar/{HOY}", json=COMPLETO)
    assert r.status_code == 200

    r = client.get(f"/api/bienestar/{HOY}")
    assert r.status_code == 200
    registro = r.json()["registro"]
    assert registro["calidad_sueno"] == 4
    assert registro["molestias_fisicas"] == 5
    assert registro["zonas_molestias"] == ["lumbar", "rodillas"]
    assert registro["estres_previsto"] == 5
    assert registro["observaciones"] == "Dormí mal por el calor"


def test_registro_parcial(client):
    r = client.put(f"/api/bienestar/{HOY}", json={"calidad_sueno": 2})
    assert r.status_code == 200
    registro = client.get(f"/api/bienestar/{HOY}").json()["registro"]
    assert registro["calidad_sueno"] == 2
    assert registro["recuperacion_fisica"] is None
    assert registro["molestias_fisicas"] is None


def test_un_registro_por_fecha_y_editable(client):
    client.put(f"/api/bienestar/{AYER}", json={"calidad_sueno": 3})
    client.put(f"/api/bienestar/{AYER}", json={"calidad_sueno": 5, "energia_fisica": 4})
    registro = client.get(f"/api/bienestar/{AYER}").json()["registro"]
    assert registro["calidad_sueno"] == 5
    assert registro["energia_fisica"] == 4


def test_dia_sin_registro_es_null_no_cero(client):
    r = client.get(f"/api/bienestar/{AYER}")
    assert r.status_code == 200
    assert r.json()["registro"] is None


def test_lista_distingue_dias_sin_registro(client):
    client.put(f"/api/bienestar/{AYER}", json={"calidad_sueno": 1})
    r = client.get("/api/bienestar?dias=3")
    assert r.status_code == 200
    dias = r.json()["dias"]
    assert [d["fecha"] for d in dias] == [HOY, AYER, (date.today() - timedelta(days=2)).isoformat()]
    assert dias[0]["registro"] is None
    assert dias[1]["registro"]["calidad_sueno"] == 1
    assert dias[2]["registro"] is None


def test_zonas_se_limpian_sin_molestias(client):
    r = client.put(
        f"/api/bienestar/{HOY}", json={"molestias_fisicas": 0, "zonas_molestias": ["lumbar"]}
    )
    assert r.status_code == 200
    registro = client.get(f"/api/bienestar/{HOY}").json()["registro"]
    assert registro["zonas_molestias"] == []


def test_validacion_de_rangos(client):
    assert client.put(f"/api/bienestar/{HOY}", json={"calidad_sueno": 0}).status_code == 422
    assert client.put(f"/api/bienestar/{HOY}", json={"calidad_sueno": 6}).status_code == 422
    assert client.put(f"/api/bienestar/{HOY}", json={"molestias_fisicas": 11}).status_code == 422
    assert (
        client.put(f"/api/bienestar/{HOY}", json={"zonas_molestias": ["codo"]}).status_code == 422
    )


def test_fecha_invalida_o_futura(client):
    assert client.get("/api/bienestar/ayer").status_code == 422
    futuro = (date.today() + timedelta(days=1)).isoformat()
    assert client.put(f"/api/bienestar/{futuro}", json={}).status_code == 422


def test_aislamiento_entre_usuarios(app, client):
    client.put(f"/api/bienestar/{HOY}", json=COMPLETO)
    with conectar(app.state.db_path) as conn:
        alta_usuario(conn, "otra", "password123456")
    with TestClient(app) as c2:
        r = c2.post("/api/auth/login", json={"username": "otra", "password": "password123456"})
        assert r.status_code == 200
        assert c2.get(f"/api/bienestar/{HOY}").json()["registro"] is None
        assert all(d["registro"] is None for d in c2.get("/api/bienestar?dias=7").json()["dias"])


def test_export_incluye_bienestar(client):
    client.put(f"/api/bienestar/{HOY}", json=COMPLETO)
    r = client.get("/api/export")
    assert r.status_code == 200
    checkins = r.json()["datos"]["morning_checkins"]
    assert len(checkins) == 1
    assert checkins[0]["calidad_sueno"] == 4


def test_sin_autenticacion(app):
    with TestClient(app) as c:
        assert c.get(f"/api/bienestar/{HOY}").status_code == 401
        assert c.put(f"/api/bienestar/{HOY}", json={}).status_code == 401
