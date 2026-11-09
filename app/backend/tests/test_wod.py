"""Tests del formato WOD del bloque B3 (docs/16).

Un WOD no es una familia nueva: es la forma que puede tomar el bloque B3
cuando el atleta declara preferencia `acondicionamiento` (bajo demanda), en
familia A (EMOM suave) o B (AMRAP). Las reglas duras (D3-D5), el presupuesto
por dimensión y la regla 1 de patrones aplican igual que al resto de la sesión.
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from fitlosophy import (
    DailyState,
    PerformedExercise,
    PerformedSession,
    Proposal,
    decide,
    generate,
    load_default_catalog,
    load_default_perfil,
)
from fitlosophy.catalog import DIMENSIONES
from fitlosophy.generator import _dosis_estacion
from fitlosophy_api.app import create_app
from fitlosophy_api.db import conectar
from fitlosophy_api.usuarios import alta_usuario

USUARIO = "atleta"
PASSWORD = "secreto123456"

AHORA = datetime(2026, 11, 9, 9, 0)


@pytest.fixture(scope="module")
def catalog():
    return load_default_catalog()


@pytest.fixture(scope="module")
def perfil():
    return load_default_perfil()


def _estado(preferencia="acondicionamiento", bjj="no", **kwargs):
    return DailyState(
        fecha=AHORA,
        recuperacion="verde",
        dolor=0,
        bjj_disponible=bjj,
        preferencia=preferencia,
        **kwargs,
    )


def _prop_minima(familia: str) -> Proposal:
    """Propuesta con presupuestos holgados para aislar el comportamiento del WOD."""
    return Proposal(
        fecha=AHORA,
        familia=familia,
        presupuestos={d: 8.0 for d in DIMENSIONES},
        patrones_prioritarios=[],
    )


def _estaciones(sesion):
    return sesion.items_bloque("B3")


# --- Generación bajo demanda -----------------------------------------------------


def test_wod_amrap_en_familia_b(catalog, perfil):
    estado = _estado()
    prop = decide(estado, [], catalog)
    assert prop.familia == "B"
    sesion = generate(prop, estado, catalog, perfil.material)
    assert sesion.wod is not None
    assert sesion.wod.tipo == "amrap"
    assert sesion.wod.minutos == 15
    assert sesion.wod.rpe_objetivo == "7-8"
    estaciones = _estaciones(sesion)
    assert 2 <= len(estaciones) <= 3
    assert sesion.valida, sesion.violaciones
    assert any("WOD" in n for n in sesion.notas)


def test_sin_preferencia_b3_clasico(catalog, perfil):
    estado = _estado(preferencia="fuerza")
    prop = decide(estado, [], catalog)
    sesion = generate(prop, estado, catalog, perfil.material)
    assert sesion.wod is None
    b3 = _estaciones(sesion)
    assert len(b3) == 1  # acondicionamiento clásico por series


def test_wod_emom_suave_en_familia_a(catalog, perfil):
    estado = _estado(bjj="si", tipo_bjj="normal")
    prop = decide(estado, [], catalog)
    assert prop.familia == "A"
    sesion = generate(prop, estado, catalog, perfil.material)
    assert sesion.wod is not None
    assert sesion.wod.tipo == "emom"
    assert sesion.wod.minutos == 12
    assert sesion.wod.rpe_objetivo == "5-6"
    assert sesion.valida, sesion.violaciones


def test_familia_c_nunca_tiene_wod(catalog, perfil):
    estado = DailyState(
        fecha=AHORA, recuperacion="rojo", dolor=0, bjj_disponible="no",
        preferencia="acondicionamiento",
    )
    prop = decide(estado, [], catalog)
    assert prop.familia == "C"
    sesion = generate(prop, estado, catalog, perfil.material)
    assert sesion.wod is None
    assert _estaciones(sesion) == []


def test_sin_presupuesto_de_cardio_no_hay_wod(catalog, perfil):
    estado = _estado()
    prop = _prop_minima("B")
    prop.presupuestos["cardio"] = 0.0
    sesion = generate(prop, estado, catalog, perfil.material)
    assert sesion.wod is None
    assert any("presupuesto de cardio" in n for n in sesion.notas)


# --- Seguridad y reglas del modelo --------------------------------------------------


def test_estaciones_respitan_seguridad_lumbar_y_regla_1(catalog, perfil):
    estado = _estado()
    prop = decide(estado, [], catalog)
    sesion = generate(prop, estado, catalog, perfil.material)
    assert sesion.wod is not None
    estaciones = _estaciones(sesion)
    patrones_b3 = set()
    for item in estaciones:
        ej = catalog[item.exercise_id]
        assert ej.impacto_lumbar != "rojo"  # docs/16: rojos fuera del formato siempre
        assert ej.patron not in patrones_b3
        patrones_b3.add(ej.patron)
    # Regla 1: B1/B2 no repiten los patrones del WOD (se construye antes).
    patrones_resto = {
        catalog[i.exercise_id].patron for i in sesion.items if i.bloque in ("B1", "B2")
    }
    assert not (patrones_b3 & patrones_resto)


def test_estaciones_familia_a_sin_explosivos_ni_agarre(catalog, perfil):
    estado = _estado(bjj="si", tipo_bjj="normal")
    prop = decide(estado, [], catalog)
    sesion = generate(prop, estado, catalog, perfil.material)
    for item in _estaciones(sesion):
        ej = catalog[item.exercise_id]
        assert ej.impacto_lumbar == "verde"
        assert not ej.explosivo
        assert ej.coste("agarre") in (None, "bajo")  # sin coste declarado = no fatiga de agarre


def test_wod_nunca_repite_patron_principal_entre_estaciones(catalog, perfil):
    """Regresión: con variedad forzada se elegían sentadilla libre y búlgara
    (ambas `dominante_rodilla`) porque solo se alternaba el grupo muscular.
    La regla 1 vale también dentro del WOD y la sesión debe salir válida."""
    ayer = AHORA - timedelta(days=1)
    historial = [
        PerformedSession(
            ayer,
            [
                PerformedExercise(x)
                for x in (
                    "pushup-classic", "goblet-squat", "rope-technical",
                    "plank-front", "side-plank", "bird-dog", "dead-bug", "pallof-press",
                )
            ],
        )
    ]
    estado = _estado(bjj="si", tipo_bjj="tecnico")
    prop = decide(estado, historial, catalog)
    sesion = generate(prop, estado, catalog, perfil.material, historial)
    assert sesion.wod is not None
    patrones = [catalog[i.exercise_id].patron for i in _estaciones(sesion)]
    assert len(patrones) == len(set(patrones)), patrones
    assert sesion.valida, sesion.violaciones


def test_duracion_y_recorte_eliminian_el_wod_entero(catalog, perfil):
    estado = _estado(tiempo_disponible=25)
    prop = decide(estado, [], catalog)
    completa = generate(prop, _estado(), catalog, perfil.material)
    assert completa.wod is not None
    sesion = generate(prop, estado, catalog, perfil.material)
    assert sesion.wod is None
    assert _estaciones(sesion) == []
    assert any("WOD completo" in n for n in sesion.notas)
    assert sesion.duracion_estimada_min <= 25


def test_sustitucion_de_estacion_conserva_dosis_wod(catalog, perfil):
    """La dosis de estación es de formato (repeticiones/segundos por ronda),
    nunca «series × repeticiones» de la dosificación clásica."""
    estado = _estado()
    prop = decide(estado, [], catalog)
    sesion = generate(prop, estado, catalog, perfil.material)
    assert sesion.wod is not None
    for item in _estaciones(sesion):
        assert "×" not in item.dosis
    # La fórmula de estación tampoco la produce para nadie del catálogo.
    for ej in catalog:
        if ej.prescripcion:
            assert "×" not in _dosis_estacion(ej, "amrap")
            assert "×" not in _dosis_estacion(ej, "emom")


# --- Dosificación de estaciones (provisional) ----------------------------------------


def test_dosis_estacion():
    """La estación parte del extremo bajo de una serie: ×1.0 en AMRAP, ×0.8
    en EMOM (se repite varias veces por sesión, docs/16)."""
    catalog = load_default_catalog()
    squat = catalog.get("squat-libre")  # repeticiones [15, 25]
    assert _dosis_estacion(squat, "amrap") == "15 repeticiones"
    assert _dosis_estacion(squat, "emom") == "12 repeticiones"
    rope = catalog.get("rope-technical")  # 100 saltos
    assert _dosis_estacion(rope, "amrap") == "100 saltos"
    assert _dosis_estacion(rope, "emom") == "80 saltos"
    goblet = catalog.get("goblet-squat")  # repeticiones [8, 15]
    assert _dosis_estacion(goblet, "amrap") == "8 repeticiones"
    assert _dosis_estacion(goblet, "emom") == "6 repeticiones"


# --- API: persistencia y flujo --------------------------------------------------------


@pytest.fixture()
def app(tmp_path):
    aplicacion = create_app(tmp_path / "test.db")
    with conectar(aplicacion.state.db_path) as conn:
        aplicacion.state.user_id = alta_usuario(conn, USUARIO, PASSWORD)
    return aplicacion


@pytest.fixture()
def client(app):
    with TestClient(app) as c:
        r = c.post("/api/auth/login", json={"username": USUARIO, "password": PASSWORD})
        assert r.status_code == 200
        yield c


def _crear_propuesta(client, **estado):
    base = {"recuperacion": "verde", "dolor": 0, "bjj_disponible": "no"}
    base.update(estado)
    r = client.post("/api/estado-diario", json=base)
    assert r.status_code == 201, r.text
    return r.json()["propuesta"]


def test_api_propuesta_y_sesion_exponen_el_wod(client):
    propuesta = _crear_propuesta(client, preferencia="acondicionamiento")
    assert propuesta["wod"] is not None, "la propuesta con preferencia acondicionamiento debe tener WOD"
    wod = propuesta["wod"]
    estaciones_api = {e["exercise_id"] for e in wod["estaciones"]}
    items_b3 = {i["exercise_id"] for i in propuesta["items"] if i["bloque"] == "B3"}
    assert estaciones_api == items_b3
    assert wod["descripcion"]

    r = client.post("/api/sesiones", json={"proposal_id": propuesta["id"]})
    assert r.status_code == 201, r.text
    sesion = r.json()["sesion"]
    assert sesion["wod"] is not None
    assert sesion["wod"]["tipo"] == wod["tipo"]
    # Al recargar (GET de la sesión) la cabecera WOD sigue ahí.
    r = client.get(f"/api/sesiones/{sesion['id']}")
    assert r.status_code == 200
    assert r.json()["sesion"]["wod"] is not None


def test_api_propuesta_clasica_sin_wod(client):
    propuesta = _crear_propuesta(client, preferencia="fuerza")
    assert propuesta["wod"] is None


def test_api_rondas_y_pesos_del_wod(client):
    """El marcador del AMRAP y el peso de las estaciones se persisten y
    vuelven en la lectura de la sesión (análisis de datos, docs/16)."""
    propuesta = _crear_propuesta(client, preferencia="acondicionamiento")
    assert propuesta["wod"]["tipo"] in ("amrap", "emom")
    if propuesta["wod"]["tipo"] == "emom":
        pytest.skip("el estado diario dio familia A (EMOM): sin rondas que registrar")

    r = client.post("/api/sesiones", json={"proposal_id": propuesta["id"]})
    sesion = r.json()["sesion"]
    estaciones = [i for i in sesion["items"] if i["bloque"] == "B3"]
    assert estaciones

    # Peso de una estación con kettlebell: 12 kg por kettlebell × 2 = 24 kg.
    con_peso = next((i for i in estaciones if i["admite_peso"]), None)
    if con_peso is not None:
        r = client.patch(
            f"/api/sesiones/{sesion['id']}/items/{con_peso['id']}",
            json={"estado": "completado", "carga_kg_real": 12, "unidades_carga": 2},
        )
        assert r.status_code == 200, r.text

    r = client.post(f"/api/sesiones/{sesion['id']}/finalizar", json={"rpe_real": 8})
    assert r.status_code == 200, r.text
    r = client.post(
        f"/api/sesiones/{sesion['id']}/cierre",
        json={"sensacion": "como_previsto", "molestias": [], "rondas_completadas": 7},
    )
    assert r.status_code == 201, r.text

    detalle = client.get(f"/api/sesiones/{sesion['id']}").json()["sesion"]
    assert detalle["cierre"]["rondas_completadas"] == 7
    if con_peso is not None:
        item = next(i for i in detalle["items"] if i["id"] == con_peso["id"])
        assert item["real"]["carga_kg"] == 12
        assert item["real"]["unidades"] == 2
        assert item["real"]["carga_total_kg"] == 24


def test_api_rondas_sin_wod_amrap_es_422(client):
    """Sin WOD (o en EMOM) no hay marcador de rondas que registrar."""
    propuesta = _crear_propuesta(client, preferencia="fuerza")
    assert propuesta["wod"] is None
    r = client.post("/api/sesiones", json={"proposal_id": propuesta["id"]})
    sesion = r.json()["sesion"]
    client.post(f"/api/sesiones/{sesion['id']}/finalizar", json={"rpe_real": 7})
    r = client.post(
        f"/api/sesiones/{sesion['id']}/cierre",
        json={"sensacion": "como_previsto", "molestias": [], "rondas_completadas": 5},
    )
    assert r.status_code == 422


def test_api_rondas_negativas_es_422(client):
    propuesta = _crear_propuesta(client, preferencia="acondicionamiento")
    r = client.post("/api/sesiones", json={"proposal_id": propuesta["id"]})
    sesion = r.json()["sesion"]
    client.post(f"/api/sesiones/{sesion['id']}/finalizar", json={"rpe_real": 8})
    r = client.post(
        f"/api/sesiones/{sesion['id']}/cierre",
        json={"sensacion": "como_previsto", "molestias": [], "rondas_completadas": -1},
    )
    assert r.status_code == 422


def test_api_preferencia_fuera_de_dominio_es_422(client):
    """La preferencia es vocabulario cerrado (docs/03): un valor libre se
    rechaza en la puerta en vez de ignorarse en silencio en el motor."""
    r = client.post(
        "/api/estado-diario",
        json={
            "recuperacion": "verde",
            "dolor": 0,
            "bjj_disponible": "no",
            "preferencia": "cardio",
        },
    )
    assert r.status_code == 422
