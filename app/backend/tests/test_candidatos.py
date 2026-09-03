"""Tests de la importación y revisión de candidatos (docs/15).

Cubre: importación idempotente, filtro por material del perfil, inferencia
dentro de los dominios de `valores`, endpoints con auth, aceptación que escribe
un YAML válido **en una copia temporal** (nunca el `data/ejercicios.yaml` real)
y descarte.
"""

import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from fitlosophy.catalog import load_default_catalog, load_default_perfil
from fitlosophy_api.app import create_app
from fitlosophy_api.candidatos import DATA_DIR, inferir_etiquetas, material_para_equipment
from fitlosophy_api.db import conectar
from fitlosophy_api.usuarios import alta_usuario

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from importar_candidatos import importar  # noqa: E402

USUARIO = "atleta"
PASSWORD = "secreto123456"

DATASET = [
    {
        "id": "0001",
        "name": "kettlebell goblet squat",
        "category": "upper legs",
        "body_part": "upper legs",
        "equipment": "kettlebell",
        "instructions": {"es": "Sujeta la kettlebell al pecho. Baja en sentadilla profunda y sube."},
        "muscle_group": "quadriceps",
        "secondary_muscles": ["glutes"],
        "media_id": "abc123",
    },
    {
        "id": "0002",
        "name": "cable fly",
        "category": "chest",
        "body_part": "chest",
        "equipment": "cable",
        "instructions": {"es": "Cruza los brazos al frente."},
        "muscle_group": "chest",
        "secondary_muscles": [],
        "media_id": None,
    },
    {
        "id": "0003",
        "name": "plank",
        "category": "waist",
        "body_part": "waist",
        "equipment": "body weight",
        "instructions": {"es": "Apoya antebrazos y puntas de los pies. Mantén la línea del cuerpo."},
        "muscle_group": "core",
        "secondary_muscles": [],
        "media_id": None,
    },
]


@pytest.fixture()
def app(tmp_path):
    aplicacion = create_app(tmp_path / "test.db")
    with conectar(aplicacion.state.db_path) as conn:
        alta_usuario(conn, USUARIO, PASSWORD)
    # La aceptación escribe en una copia temporal: el catálogo real no se toca.
    copia = tmp_path / "ejercicios.yaml"
    shutil.copy2(DATA_DIR / "ejercicios.yaml", copia)
    aplicacion.state.ejercicios_path = str(copia)
    return aplicacion


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        r = c.post("/api/auth/login", json={"username": USUARIO, "password": PASSWORD})
        assert r.status_code == 200
        yield c


@pytest.fixture()
def dataset_json(tmp_path):
    ruta = tmp_path / "exercises.json"
    ruta.write_text(json.dumps(DATASET), encoding="utf-8")
    return ruta


def _importar(app, dataset_json):
    with conectar(app.state.db_path) as conn:
        return importar(conn, dataset_json, videos_dir=tmp_path_sin_gifs(dataset_json))


def tmp_path_sin_gifs(ruta: Path) -> Path:
    """Directorio inexistente: el importador debe seguir sin GIFs."""
    return ruta.parent / "sin-videos"


# --- Lógica pura ---------------------------------------------------------------------


def test_filtro_material(dataset_json, app):
    """Solo entra lo ejecutable con el inventario de data/perfil.yaml."""
    with conectar(app.state.db_path) as conn:
        res = importar(conn, dataset_json, videos_dir=tmp_path_sin_gifs(dataset_json))
    assert res["importados"] == 2  # kettlebell y body weight; el de cable, no
    assert res["descartados_material"] == 1
    assert res["por_equipment"] == {"kettlebell": 1, "body weight": 1}


def test_importacion_idempotente(dataset_json, app):
    with conectar(app.state.db_path) as conn:
        importar(conn, dataset_json, videos_dir=tmp_path_sin_gifs(dataset_json))
        res = importar(conn, dataset_json, videos_dir=tmp_path_sin_gifs(dataset_json))
        n = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]
    assert res["importados"] == 0
    assert res["ya_presentes"] == 3 - 1  # los dos importados la primera vez
    assert n == 2


def test_inferencia_dentro_de_dominios():
    """El borrador inferido respeta los dominios de `valores` (docs/15)."""
    valores = load_default_catalog().valores
    perfil = load_default_perfil()
    for reg in DATASET:
        material = material_para_equipment(reg["equipment"], reg["name"], set(perfil.material))
        if material is None:
            continue
        et = inferir_etiquetas(reg, material)
        assert et["patron"] in valores["patron"]
        assert et["nivel"] in valores["nivel"]
        assert et["lateralidad"] in valores["lateralidad"]
        assert et["impacto_lumbar"] in valores["impacto_lumbar"]
        assert et["compatibilidad_bjj"] in valores["compatibilidad_bjj"]
        assert all(d in valores["dimensiones"] for d in et["coste_dimensiones"])
        assert all(v in valores["nivel_coste"] for v in et["coste_dimensiones"].values())


def test_inferencia_reglas_clave():
    """Las reglas conservadoras: squat con KB es dominante de rodilla, la
    plancha es antiextensión verde, el swing es bisagra roja."""
    squat = inferir_etiquetas(DATASET[0], ["kettlebell"])
    assert squat["patron"] == "dominante_rodilla"
    plancha = inferir_etiquetas(DATASET[2], [])
    assert plancha["patron"] == "core_antiextension"
    assert plancha["impacto_lumbar"] == "verde"
    assert plancha["prescripcion"].get("segundos")
    swing = inferir_etiquetas(
        {"name": "kettlebell swing", "body_part": "upper legs", "muscle_group": "glutes",
         "equipment": "kettlebell", "instructions": {"es": "Bisagra de cadera."}},
        ["kettlebell"],
    )
    assert swing["patron"] == "dominante_cadera"
    assert swing["impacto_lumbar"] == "rojo"
    assert "lumbar" in swing["descripcion"].lower()


# --- Endpoints -----------------------------------------------------------------------


def test_endpoints_exigen_sesion(app):
    with TestClient(app) as c:
        assert c.get("/api/candidatos").status_code == 401
        assert c.get("/api/candidatos/1").status_code == 401
        assert c.get("/api/candidatos/1/gif").status_code == 401
        assert c.put("/api/candidatos/1", json={"etiquetas_finales": {}}).status_code == 401
        assert c.post("/api/candidatos/1/aceptar").status_code == 401
        assert c.post("/api/candidatos/1/descartar", json={}).status_code == 401


def test_candidato_inexistente_404(client):
    assert client.get("/api/candidatos/999").status_code == 404
    assert client.post("/api/candidatos/999/aceptar").status_code == 404
    assert client.post("/api/candidatos/999/descartar", json={}).status_code == 404


def test_listado_y_detalle(client, app, dataset_json):
    _importar(app, dataset_json)
    r = client.get("/api/candidatos")
    assert r.status_code == 200
    cuerpo = r.json()
    assert len(cuerpo["candidatos"]) == 2
    assert cuerpo["contadores"]["equipment"] == {"kettlebell": 1, "body weight": 1}

    r = client.get("/api/candidatos", params={"equipment": "kettlebell"})
    assert len(r.json()["candidatos"]) == 1

    cid = r.json()["candidatos"][0]["id"]
    det = client.get(f"/api/candidatos/{cid}").json()
    assert det["nombre_en"] == "kettlebell goblet squat"
    assert det["etiquetas_inferidas"]["patron"] == "dominante_rodilla"
    assert det["etiquetas_finales"] is None
    assert "valores" in det
    # Sin GIF importado, el endpoint responde 404.
    assert client.get(f"/api/candidatos/{cid}/gif").status_code == 404


def test_guardar_etiquetas_valida_dominios(client, app, dataset_json):
    _importar(app, dataset_json)
    cid = client.get("/api/candidatos").json()["candidatos"][0]["id"]
    r = client.put(f"/api/candidatos/{cid}", json={"etiquetas_finales": {"impacto_lumbar": "morado"}})
    assert r.status_code == 422
    r = client.put(
        f"/api/candidatos/{cid}",
        json={"etiquetas_finales": {"impacto_lumbar": "amarillo", "nivel": "intermedio"}},
    )
    assert r.status_code == 200
    assert r.json()["etiquetas_finales"]["nivel"] == "intermedio"


def test_aceptar_escribe_yaml_valido(client, app, dataset_json):
    _importar(app, dataset_json)
    cid = client.get("/api/candidatos", params={"equipment": "kettlebell"}).json()["candidatos"][0]["id"]
    r = client.post(f"/api/candidatos/{cid}/aceptar")
    assert r.status_code == 200, r.text
    exercise_id = r.json()["exercise_id"]
    assert exercise_id.startswith("kettlebell-goblet-squat")

    # La copia temporal es YAML válido y contiene la entrada; el real, intacto.
    ruta_copia = Path(app.state.ejercicios_path)
    datos = yaml.safe_load(ruta_copia.read_text(encoding="utf-8"))
    nuevo = next(e for e in datos["exercises"] if e["id"] == exercise_id)
    assert nuevo["patron"] == "dominante_rodilla"
    assert nuevo["material"] == ["kettlebell"]
    assert all(e["id"] != exercise_id for e in yaml.safe_load((DATA_DIR / "ejercicios.yaml").read_text(encoding="utf-8"))["exercises"])

    # El catálogo en memoria ya lo incluye y el candidato queda aceptado.
    assert app.state.catalog.get(exercise_id) is not None
    det = client.get(f"/api/candidatos/{cid}").json()
    assert det["estado"] == "aceptado"
    assert det["revisado_por"] is not None
    # No se puede revisar dos veces.
    assert client.post(f"/api/candidatos/{cid}/aceptar").status_code == 409


def test_aceptar_devuelve_422_si_no_valida(client, app, dataset_json):
    _importar(app, dataset_json)
    cid = client.get("/api/candidatos").json()["candidatos"][0]["id"]
    # Etiquetas editadas que no pasan la puerta: prescripción mal formada.
    r = client.put(
        f"/api/candidatos/{cid}",
        json={"etiquetas_finales": {"prescripcion": {"series": [5, 3]}}},
    )
    assert r.status_code == 200
    r = client.post(f"/api/candidatos/{cid}/aceptar")
    assert r.status_code == 422
    assert "errores" in r.json()["detail"]


def test_descartar(client, app, dataset_json):
    _importar(app, dataset_json)
    cid = client.get("/api/candidatos").json()["candidatos"][0]["id"]
    r = client.post(f"/api/candidatos/{cid}/descartar", json={"motivo": "duplica al catálogo"})
    assert r.status_code == 200
    det = client.get(f"/api/candidatos/{cid}").json()
    assert det["estado"] == "descartado"
    assert det["motivo_descarte"] == "duplica al catálogo"
    pendientes = client.get("/api/candidatos", params={"estado": "pendiente_revision"}).json()
    assert all(c["id"] != cid for c in pendientes["candidatos"])
