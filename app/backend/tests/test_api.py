"""Tests de la API del MVP (docs/14) con fastapi.testclient.

Cada test usa una BD temporal propia. El flujo de referencia (criterio 2):
estado diario → propuesta → aceptar → marcar ítems → Finalizar → cierre →
historial actualizado, con la carga del día siguiente calculada desde la
persistencia y la dosis real.
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from fitlosophy.load import compute_load
from fitlosophy_api.app import create_app
from fitlosophy_api.auth import crear_usuario
from fitlosophy_api.history import construir_historial

USUARIO = "atleta"
PASSWORD = "secreto123"


@pytest.fixture()
def app(tmp_path):
    aplicacion = create_app(tmp_path / "test.db")
    crear_usuario(aplicacion.state.db, USUARIO, PASSWORD)
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


def _ejecutar_sesion(client, propuesta, rpe=7):
    """Acepta la propuesta y completa la sesión con el marcado por defecto."""
    r = client.post("/api/sesiones", json={"proposal_id": propuesta["id"]})
    assert r.status_code == 201, r.text
    sesion = r.json()["sesion"]
    r = client.post(f"/api/sesiones/{sesion['id']}/finalizar", json={"rpe_real": rpe})
    assert r.status_code == 200, r.text
    return r.json()


# --- Criterio 9: acceso protegido -------------------------------------------------


def test_acceso_exige_sesion(app):
    with TestClient(app) as c:
        assert c.get("/api/perfil").status_code == 401
        assert c.get("/api/historial").status_code == 401
        assert c.post("/api/estado-diario", json={"recuperacion": "verde", "dolor": 0, "bjj_disponible": "no"}).status_code == 401
        assert c.post("/api/auth/login", json={"username": USUARIO, "password": "incorrecta"}).status_code == 401
        r = c.post("/api/auth/login", json={"username": USUARIO, "password": PASSWORD})
        assert r.status_code == 200
        assert "fitlosophy_session" in r.cookies
        assert c.get("/api/auth/me").json()["username"] == USUARIO
        assert c.post("/api/auth/logout").status_code == 200
        assert c.get("/api/auth/me").status_code == 401


# --- Criterio 2 (+ 3, 4 y 6): flujo completo extremo a extremo ----------------------


def test_flujo_completo_estado_a_historial(client):
    # 1. Estado diario → propuesta con familia, explicación e ítems (criterio 6).
    propuesta = _crear_propuesta(client, preferencia="fuerza")
    assert propuesta["familia"] == "B"  # día verde sin BJJ ni historial
    assert propuesta["explicacion"]
    assert propuesta["reglas_aplicadas"]
    assert "incertidumbres" in propuesta
    assert propuesta["items"]
    assert all(i["dosis"] for i in propuesta["items"])
    assert propuesta["rpe_previsto"] == "7-8"
    assert propuesta["valida"]

    # 2. Aceptar → sesión en curso con ítems marcables.
    r = client.post("/api/sesiones", json={"proposal_id": propuesta["id"]})
    assert r.status_code == 201
    sesion = r.json()["sesion"]
    assert sesion["estado"] == "en_curso"
    assert all(i["estado"] == "pendiente" for i in sesion["items"])
    b1 = [i for i in sesion["items"] if i["bloque"] == "B1"]
    swing = next(i for i in b1 if i["exercise_id"] == "kb-swing-two-hand")

    # 3. Marcado: check (una acción), modificado (solo lo que cambió), no realizado.
    ultimo = b1[-1]
    r = client.patch(f"/api/sesiones/{sesion['id']}/items/{b1[1]['id']}", json={"estado": "completado"})
    assert r.status_code == 200
    r = client.patch(
        f"/api/sesiones/{sesion['id']}/items/{swing['id']}",
        json={"estado": "modificado", "series_real": 11},  # por encima del rango [6, 10]
    )
    assert r.status_code == 200
    r = client.patch(
        f"/api/sesiones/{sesion['id']}/items/{ultimo['id']}",
        json={"estado": "no_realizado", "motivo": "sin tiempo"},
    )
    assert r.status_code == 200

    # 4. Finalizar: cierra la ejecución y recalcula el impacto con la dosis real.
    r = client.post(f"/api/sesiones/{sesion['id']}/finalizar", json={"rpe_real": 8})
    assert r.status_code == 200
    puntos_real = r.json()["puntos_sesion_real"]
    # Swing modificado (series 11 > 10): ×1.25 sobre bisagra 3 (docs/12).
    assert puntos_real["bisagra"] == pytest.approx(3.75)
    assert puntos_real["lumbar"] == pytest.approx(2.5)  # swing 2 × 1.25
    sesion = r.json()["sesion"]
    assert sesion["estado"] == "finalizada"
    estados = {i["exercise_id"]: i["estado"] for i in sesion["items"]}
    assert estados["kb-swing-two-hand"] == "modificado"
    assert estados[ultimo["exercise_id"]] == "no_realizado"
    # Los ítems sin marcar se dieron por completados (check por defecto).
    assert all(i["estado"] != "pendiente" for i in sesion["items"])
    assert all(i["puntos_reales"] is not None for i in sesion["items"])

    # 5. Cierre: sensación + molestias.
    r = client.post(
        f"/api/sesiones/{sesion['id']}/cierre",
        json={"sensacion": "mas_duro", "molestias": []},
    )
    assert r.status_code == 201

    # 6. Historial actualizado: el día refleja física; el detalle muestra
    # propuesta vs realizado y RPE previsto/real.
    hoy = datetime.now().date().isoformat()
    r = client.get("/api/historial", params={"dias": 3})
    dia = next(d for d in r.json()["dias"] if d["fecha"] == hoy)
    assert "fisica" in dia["tipos"]
    r = client.get(f"/api/historial/{hoy}")
    detalle = r.json()
    assert detalle["propuestas"] and detalle["sesiones"]
    assert detalle["propuestas"][0]["rpe_previsto"] == "7-8"
    assert detalle["sesiones"][0]["rpe_real"] == 8

    # 7. Criterio 4: la carga del día siguiente se calcula con la dosis real.
    propuesta2 = _crear_propuesta(client)
    carga = propuesta2["carga"]["puntos"]
    assert carga["bisagra"] == pytest.approx(puntos_real["bisagra"])  # 3.75
    assert carga["empuje"] == pytest.approx(puntos_real["empuje"])


def test_flujo_completo_con_bjj_y_sustitucion_en_ejecucion(client, app):
    """Criterio 2 por el camino con BJJ (familia A), incluyendo la vía de
    sustitución en ejecución (docs/14: las adaptaciones del gimnasio se
    registran como sustituciones) y el cierre con congelación de ventana."""

    # 1. El usuario declara el BJJ del día (docs/14: se declara cada día).
    hoy = datetime.now().date().isoformat()
    r = client.post("/api/bjj", json={"clasificacion": "normal", "duracion_minutos": 75})
    assert r.status_code == 201

    # 2. Estado diario con BJJ normal → familia A (compatible, docs/03).
    propuesta = _crear_propuesta(client, bjj_disponible="si", tipo_bjj="normal")
    assert propuesta["familia"] == "A"
    assert propuesta["valida"]
    assert propuesta["explicacion"]
    assert propuesta["items"]

    # 3. Aceptar → sesión en curso con ítems marcables.
    r = client.post("/api/sesiones", json={"proposal_id": propuesta["id"]})
    assert r.status_code == 201
    sesion = r.json()["sesion"]
    assert sesion["estado"] == "en_curso"
    items = sesion["items"]
    assert len(items) >= 3
    assert all(i["estado"] == "pendiente" for i in items)

    # 4. Marcado por las cuatro vías del modal (docs/14 §3).
    #    a) Check: completado tal cual (una sola acción).
    r = client.patch(f"/api/sesiones/{sesion['id']}/items/{items[0]['id']}", json={"estado": "completado"})
    assert r.status_code == 200

    #    b) Sustituido: ejercicio real del catálogo (adaptación del gimnasio).
    #       Se elige un sustituto declarado del ejercicio o, si no hay, otro del
    #       mismo patrón; la ejecución registra, no rechaza (docs/14).
    catalog = app.state.catalog
    sust_item = None
    sustituto = None
    for it in items[1:]:
        ej = catalog[it["exercise_id"]]
        candidato = next((c for c in ej.sustitutos if catalog.get(c) is not None), None)
        if candidato is None:
            mismo_patron = [e for e in catalog.ejercicios if e.id != ej.id and e.patron == ej.patron]
            candidato = mismo_patron[0].id if mismo_patron else None
        if candidato:
            sust_item = it
            sustituto = candidato
            break
    assert sust_item is not None, "la sesión debería tener algún ítem sustituible"
    r = client.patch(
        f"/api/sesiones/{sesion['id']}/items/{sust_item['id']}",
        json={"estado": "sustituido", "exercise_id_real": sustituto, "motivo": "adaptación en el gimnasio"},
    )
    assert r.status_code == 200
    assert isinstance(r.json()["advertencias"], list)

    #    c) No realizado con motivo.
    resto = [it for it in items if it["id"] not in (items[0]["id"], sust_item["id"])]
    r = client.patch(
        f"/api/sesiones/{sesion['id']}/items/{resto[-1]['id']}",
        json={"estado": "no_realizado", "motivo": "sin tiempo"},
    )
    assert r.status_code == 200

    #    d) Validaciones del esquema: sustituto sin ejercicio real y
    #       modificado sin valores reales se rechazan (422).
    r = client.patch(f"/api/sesiones/{sesion['id']}/items/{items[0]['id']}", json={"estado": "sustituido"})
    assert r.status_code == 422
    r = client.patch(f"/api/sesiones/{sesion['id']}/items/{items[0]['id']}", json={"estado": "modificado"})
    assert r.status_code == 422

    # 5. Finalizar: el sustituto entra en el recálculo con su impacto real.
    r = client.post(f"/api/sesiones/{sesion['id']}/finalizar", json={"rpe_real": 7})
    assert r.status_code == 200
    sesion = r.json()["sesion"]
    assert sesion["estado"] == "finalizada"
    assert r.json()["puntos_sesion_real"]
    sust = next(i for i in sesion["items"] if i["id"] == sust_item["id"])
    assert sust["estado"] == "sustituido"
    assert sust["exercise_id_real"] == sustituto
    assert sust["puntos_reales"]

    # 6. Cierre: molestia lumbar congela la ventana (criterio 5).
    r = client.post(
        f"/api/sesiones/{sesion['id']}/cierre",
        json={"sensacion": "mas_duro", "molestias": [{"zona": "lumbar", "intensidad": 4}]},
    )
    assert r.status_code == 201
    assert r.json()["dimensiones_congeladas"] == ["lumbar"]

    # 7. Historial: el día muestra física + BJJ; el detalle conserva el
    #    ejercicio real del ítem sustituido y el cierre (criterios 2 y 7).
    r = client.get("/api/historial", params={"dias": 3})
    dia = next(d for d in r.json()["dias"] if d["fecha"] == hoy)
    assert "fisica" in dia["tipos"]
    assert "bjj" in dia["tipos"]

    r = client.get(f"/api/historial/{hoy}")
    detalle = r.json()
    assert detalle["estados_diarios"][0]["bjj_disponible"] == "si"
    assert detalle["estados_diarios"][0]["tipo_bjj"] == "normal"
    assert detalle["bjj"][0]["clasificacion"] == "normal"
    s = next(s for s in detalle["sesiones"] if s["id"] == sesion["id"])
    assert s["cierre"]["dimensiones_congeladas"] == ["lumbar"]
    item_sust = next(i for i in s["items"] if i["id"] == sust_item["id"])
    assert item_sust["exercise_id_real"] == sustituto


def test_flujo_sin_material_e2e(client):
    """Criterio 2 en modo sin material (vacaciones/viaje, docs/14): la sesión
    se compone solo con ejercicios ejecutables sin nada y el flujo llega al
    historial."""

    # 1. Desmarcar todo = modo sin material.
    propuesta = _crear_propuesta(client, material_disponible=[])
    assert propuesta["valida"]
    assert any("pendiente" in n for n in propuesta["notas"])

    # 2. Aceptar y ejecutar sin marcar nada: el check es la acción por defecto
    #    (los ítems sin marcar se dan por completados al finalizar).
    r = client.post("/api/sesiones", json={"proposal_id": propuesta["id"]})
    assert r.status_code == 201
    sesion = r.json()["sesion"]
    assert sesion["items"]

    r = client.post(f"/api/sesiones/{sesion['id']}/finalizar", json={"rpe_real": 6})
    assert r.status_code == 200
    sesion = r.json()["sesion"]
    assert sesion["estado"] == "finalizada"
    assert all(i["estado"] == "completado" for i in sesion["items"])

    # 3. Cierre sin molestias y verificación en el historial.
    r = client.post(
        f"/api/sesiones/{sesion['id']}/cierre",
        json={"sensacion": "como_previsto", "molestias": []},
    )
    assert r.status_code == 201
    hoy = datetime.now().date().isoformat()
    r = client.get("/api/historial", params={"dias": 3})
    dia = next(d for d in r.json()["dias"] if d["fecha"] == hoy)
    assert "fisica" in dia["tipos"]


# --- Criterio 8: sustituciones en la propuesta ----------------------------------------


def test_sustitucion_invalida_rechazada_con_motivo(client):
    propuesta = _crear_propuesta(client, preferencia="fuerza")
    items = propuesta["items"]
    indice_swing = next(n for n, i in enumerate(items) if i["exercise_id"] == "kb-swing-two-hand")

    # Swing a una mano: mismo patrón pero impacto lumbar rojo > amarillo (regla 2).
    r = client.post(
        f"/api/propuestas/{propuesta['id']}/sustituir",
        json={"item_indice": indice_swing, "exercise_id": "kb-swing-one-hand"},
    )
    assert r.status_code == 409
    motivos = r.json()["detail"]["motivos"]
    assert any("lumbar" in m for m in motivos)

    # Dominada por flexión: patrón distinto (regla 1).
    indice_empuje = next(n for n, i in enumerate(items) if i["exercise_id"].startswith("pushup") or i["exercise_id"] == "pike-pushup")
    r = client.post(
        f"/api/propuestas/{propuesta['id']}/sustituir",
        json={"item_indice": indice_empuje, "exercise_id": "pullup-strict"},
    )
    assert r.status_code == 409


def test_sustitucion_valida_actualiza_propuesta(client):
    propuesta = _crear_propuesta(client, preferencia="fuerza")
    items = propuesta["items"]
    indice_remo = next(n for n, i in enumerate(items) if i["exercise_id"] == "kb-row-supported")
    r = client.post(
        f"/api/propuestas/{propuesta['id']}/sustituir",
        json={"item_indice": indice_remo, "exercise_id": "trx-row"},
    )
    assert r.status_code == 200
    nueva = r.json()["propuesta"]
    assert nueva["items"][indice_remo]["exercise_id"] == "trx-row"
    assert nueva["valida"]
    # La propuesta queda persistida: al aceptar, la sesión lleva el sustituto.
    r = client.post("/api/sesiones", json={"proposal_id": propuesta["id"]})
    assert any(i["exercise_id"] == "trx-row" for i in r.json()["sesion"]["items"])
    # Y ya no se puede sustituir sobre una propuesta aceptada.
    r = client.post(
        f"/api/propuestas/{propuesta['id']}/sustituir",
        json={"item_indice": 0, "exercise_id": "glute-bridge"},
    )
    assert r.status_code == 409


# --- Criterio 5: respuesta negativa congela la ventana (docs/12) ------------------------


def test_respuesta_negativa_congela_dimension(client, app):
    propuesta = _crear_propuesta(client, preferencia="fuerza")
    resultado = _ejecutar_sesion(client, propuesta)
    puntos_real = resultado["puntos_sesion_real"]
    sesion_id = resultado["sesion"]["id"]

    r = client.post(
        f"/api/sesiones/{sesion_id}/cierre",
        json={"sensacion": "mas_duro", "molestias": [{"zona": "lumbar", "intensidad": 4}]},
    )
    assert r.status_code == 201
    assert r.json()["dimensiones_congeladas"] == ["lumbar"]

    # 30 h después, la ventana normal decae a ×0.6 pero la lumbar queda congelada
    # a ×1.0 durante 24 h adicionales (docs/12).
    catalog = app.state.catalog
    historial = construir_historial(app.state.db, catalog)
    futuro = datetime.now() + timedelta(hours=30)
    carga = compute_load(historial, catalog, futuro)
    assert carga.puntos["lumbar"] == pytest.approx(puntos_real["lumbar"] * 1.0)
    assert carga.puntos["bisagra"] == pytest.approx(puntos_real["bisagra"] * 0.6)
    assert any("congelada" in o for o in carga.origenes["lumbar"])


def test_cierre_sin_molestias_no_congela(client):
    propuesta = _crear_propuesta(client)
    resultado = _ejecutar_sesion(client, propuesta)
    r = client.post(
        f"/api/sesiones/{resultado['sesion']['id']}/cierre",
        json={"sensacion": "como_previsto", "molestias": [{"zona": "lumbar", "intensidad": 0}]},
    )
    assert r.json()["dimensiones_congeladas"] == []


# --- BJJ: registro, corrección y efecto en la carga (criterio 7) ------------------------


def test_bjj_registro_correccion_y_carga(client):
    # BJJ duro "ayer" con edad ≤ 24 h (ventana ×1.0, docs/12). El motor usa el
    # día natural anterior para C4 (docs/03, load.py resumen_ayer), así que la
    # fecha se construye ayer a la misma hora + 1 min: siempre cae en el día
    # anterior (edad ≈ 23 h 59 min) independientemente de cuándo se ejecute el
    # test (la construcción "hace 20 h" fallaba de 20:00 a 23:59 locales).
    ahora = datetime.now()
    ayer = (
        datetime.combine((ahora - timedelta(days=1)).date(), ahora.time().replace(microsecond=0))
        + timedelta(minutes=1)
    ).isoformat()
    r = client.post("/api/bjj", json={"clasificacion": "duro", "duracion_minutos": 75, "fecha": ayer})
    assert r.status_code == 201
    registro_id = r.json()["id"]

    propuesta = _crear_propuesta(client)
    carga = propuesta["carga"]["puntos"]
    assert carga["agarre"] == pytest.approx(3.0)
    assert carga["core"] == pytest.approx(3.0)
    assert carga["lumbar"] == pytest.approx(2.0)
    assert "C4" in propuesta["reglas_aplicadas"]  # BJJ duro ayer -> techo medio

    # Corrección del registro: era técnico, no duro; la carga se recalcula.
    r = client.put(f"/api/bjj/{registro_id}", json={"clasificacion": "tecnico"})
    assert r.status_code == 200
    propuesta = _crear_propuesta(client)
    assert propuesta["carga"]["puntos"]["agarre"] == pytest.approx(1.0)


def test_correcciones_de_sesion_y_cierre(client):
    propuesta = _crear_propuesta(client)
    resultado = _ejecutar_sesion(client, propuesta, rpe=6)
    sesion_id = resultado["sesion"]["id"]
    client.post(
        f"/api/sesiones/{sesion_id}/cierre",
        json={"sensacion": "como_previsto", "molestias": []},
    )
    r = client.put(f"/api/sesiones/{sesion_id}", json={"rpe_real": 8})
    assert r.status_code == 200
    r = client.put(
        f"/api/sesiones/{sesion_id}/cierre",
        json={"molestias": [{"zona": "rodilla", "intensidad": 3}]},
    )
    assert r.status_code == 200
    assert r.json()["dimensiones_congeladas"] == ["rodilla_piernas"]
    r = client.get(f"/api/sesiones/{sesion_id}")
    assert r.json()["sesion"]["rpe_real"] == 8


# --- Perfil y exportación (criterio 7) ----------------------------------------------------


def test_perfil_get_y_put(client):
    r = client.get("/api/perfil")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "kettlebell" in r.json()["material"]
    data["persona"]["peso_kg"] = 100
    r = client.put("/api/perfil", json={"data": data})
    assert r.status_code == 200
    assert client.get("/api/perfil").json()["data"]["persona"]["peso_kg"] == 100


def test_export_completo_sin_credenciales(client):
    _crear_propuesta(client)
    client.post("/api/bjj", json={"clasificacion": "normal", "duracion_minutos": 75})
    r = client.get("/api/export")
    assert r.status_code == 200
    datos = r.json()["datos"]
    for tabla in ("daily_states", "proposals", "bjj_records", "profile"):
        assert tabla in datos
    assert datos["daily_states"] and datos["bjj_records"]
    assert "users" not in datos and "password_hash" not in r.text


# --- Material: modo sin material desde la API (regla 9 de docs/06) -----------------------


def test_modo_sin_material(client, app):
    propuesta = _crear_propuesta(client, material_disponible=[])
    catalog = app.state.catalog
    for item in propuesta["items"]:
        ej = catalog[item["exercise_id"]]
        assert ej.sin_material or all(m == "tatami" for m in ej.material)
    assert any("pendiente" in n for n in propuesta["notas"])
    r = client.post(
        "/api/estado-diario",
        json={"recuperacion": "verde", "dolor": 0, "bjj_disponible": "no", "material_disponible": ["trx"]},
    )
    assert r.status_code == 201  # 'trx' es un token válido del inventario
    r = client.post(
        "/api/estado-diario",
        json={"recuperacion": "verde", "dolor": 0, "bjj_disponible": "no", "material_disponible": ["balon medicinal"]},
    )
    assert r.status_code == 422  # token desconocido


# --- Validación del cuestionario ----------------------------------------------------------


def test_dolor_sin_zona_rechazado(client):
    r = client.post(
        "/api/estado-diario",
        json={"recuperacion": "amarillo", "dolor": 5, "bjj_disponible": "si", "tipo_bjj": "normal"},
    )
    assert r.status_code == 422
    r = client.post(
        "/api/estado-diario",
        json={"recuperacion": "amarillo", "dolor": 5, "zona_dolor": "lumbar", "bjj_disponible": "si", "tipo_bjj": "normal"},
    )
    assert r.status_code == 201
    assert r.json()["propuesta"]["familia"] == "C"  # D1
    assert "D1" in r.json()["propuesta"]["reglas_aplicadas"]
