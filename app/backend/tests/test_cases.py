"""Tests funcionales: los 10 casos de validación manual de docs/13.

Convenciones de los casos (docs/13):
- Puntos de coste: bajo=1, medio=2, alto=3; secundarios a la mitad.
- Decaimiento: 24 h ×1.0, 48 h ×0.6, 72 h ×0.3.
- Presupuesto: (8 − carga activa), ×0.5 en familia A, mínimo 0.
- Umbrales: < 4 baja, 4-8 media, > 8 alta.
"""

from datetime import datetime, timedelta

import pytest

from fitlosophy import (
    BjjRecord,
    DailyState,
    PerformedExercise,
    PerformedSession,
    SessionItem,
    SessionProposal,
    decide,
    generate,
    load_default_catalog,
    load_default_perfil,
)
from fitlosophy.generator import (
    check_substitution,
    find_substitute,
    motivos_exclusion,
    puntos_propuesta,
    validate_session,
)

AHORA = datetime(2026, 8, 3, 9, 0)  # lunes


@pytest.fixture(scope="module")
def catalog():
    return load_default_catalog()


@pytest.fixture(scope="module")
def perfil():
    return load_default_perfil()


def sesion_documentada(catalog, prop, espec):
    """Reconstruye la sesión que docs/13 documenta y la pasa por la validación
    final de docs/06. `espec`: lista de (exercise_id, bloque)."""
    items = []
    for eid, bloque in espec:
        ej = catalog[eid]
        puntos = {} if bloque in ("B0", "B4") else puntos_propuesta(
            ej, prop.familia, prop.familia in ("A", "C")
        )
        items.append(SessionItem(exercise_id=eid, bloque=bloque, dosis="", puntos=puntos))
    sesion = SessionProposal(fecha=prop.fecha, familia=prop.familia, items=items)
    return validate_session(sesion, prop, catalog)


# --- Caso 1. Día verde sin BJJ, historial ligero -> familia B ---------------------


def test_caso1_verde_sin_bjj_familia_b(catalog, perfil):
    historial = [
        PerformedSession(
            AHORA - timedelta(hours=60),  # ventana 48-72 h, ×0.3
            [
                PerformedExercise("pushup-classic"),   # empuje 1, core 1
                PerformedExercise("goblet-squat"),     # rodilla 2, core 1
                PerformedExercise("pallof-press"),     # core 1
            ],
        )
    ]
    estado = DailyState(
        fecha=AHORA, recuperacion="verde", dolor=0, bjj_disponible="no", preferencia="fuerza"
    )
    prop = decide(estado, historial, catalog)

    assert prop.familia == "B"
    assert prop.carga.niveles["empuje"] == "baja"  # 0.3
    assert prop.carga.puntos["core"] == pytest.approx(0.9)  # (1+1+1) × 0.3
    assert prop.presupuestos["empuje"] == pytest.approx(7.7)
    assert prop.presupuestos["tiron"] == pytest.approx(8.0)
    assert prop.presupuestos["agarre"] == pytest.approx(8.0)
    assert prop.presupuestos["bisagra"] == pytest.approx(8.0)
    assert prop.presupuestos["lumbar"] == pytest.approx(8.0)
    assert prop.presupuestos["rodilla_piernas"] == pytest.approx(7.4)
    assert prop.presupuestos["core"] == pytest.approx(7.1)
    assert prop.presupuestos["cardio"] == pytest.approx(8.0)

    # La sesión documentada en docs/13 pasa la validación final con los mismos
    # puntos por dimensión.
    sesion = sesion_documentada(
        catalog,
        prop,
        [
            ("dead-bug", "B0"),
            ("agility-ladder-basic", "B0"),
            ("kb-swing-two-hand", "B1"),   # 6×10: bisagra 3, lumbar 2, agarre 2, cardio 2
            ("kb-press", "B1"),            # 4×6/lado: empuje 2, core 0.5
            ("pullup-strict", "B1"),       # 12 total: tirón 2, agarre 2
            ("side-plank", "B2"),          # 3×30 s: core 1
            ("rope-technical", "B3"),      # 5×100: cardio 1, impacto 1
        ],
    )
    assert sesion.valida, sesion.violaciones
    assert sesion.puntos_sesion["bisagra"] == 3.0
    assert sesion.puntos_sesion["lumbar"] == 2.0
    assert sesion.puntos_sesion["agarre"] == 4.0
    assert sesion.puntos_sesion["empuje"] == 2.0
    assert sesion.puntos_sesion["tiron"] == 2.0
    assert sesion.puntos_sesion["core"] == 1.5
    assert sesion.puntos_sesion["cardio"] == 3.0
    assert sesion.puntos_sesion["impacto_articular"] == 1.0

    # La sesión generada automáticamente también es válida y segura (heurística
    # de selección provisional: no tiene por qué coincidir ejercicio a ejercicio).
    auto = generate(prop, estado, catalog, perfil.material)
    assert auto.valida, auto.violaciones
    assert "kb-swing-two-hand" in [i.exercise_id for i in auto.items]
    rojos = [i for i in auto.items if catalog[i.exercise_id].impacto_lumbar == "rojo"]
    assert len(rojos) <= 1  # D4 / regla 3 de composición


# --- Caso 2. BJJ normal por la tarde con lumbar, bisagra y agarre cargados ---------


def _historial_caso2():
    return [
        PerformedSession(
            AHORA - timedelta(hours=20),
            [
                PerformedExercise("kb-swing-one-hand"),   # bisagra 3, lumbar 3, agarre 3, core 1.5
                PerformedExercise("kb-deadlift"),         # bisagra 2, lumbar 2, agarre 1
                PerformedExercise("kb-row-supported"),    # tirón 2, agarre 2, core 1
            ],
        ),
        BjjRecord(AHORA - timedelta(hours=14), "normal"),
    ]


def test_caso2_bjj_normal_con_carga_familia_a(catalog, perfil):
    historial = _historial_caso2()
    estado = DailyState(fecha=AHORA, recuperacion="verde", dolor=0, bjj_disponible="si", tipo_bjj="normal")
    prop = decide(estado, historial, catalog)

    assert prop.familia == "A"
    assert prop.d3_activa
    # Presupuestos de docs/06 (umbral 8 − carga, ×0.5).
    assert prop.presupuestos["lumbar"] == pytest.approx(1.0)
    assert prop.presupuestos["bisagra"] == pytest.approx(1.0)
    assert prop.presupuestos["core"] == pytest.approx(1.75)
    assert prop.presupuestos["empuje"] == pytest.approx(4.0)
    assert prop.presupuestos["rodilla_piernas"] == pytest.approx(4.0)
    # Desviación documentada: docs/06 calcula agarre 7 -> presupuesto 0.5 porque
    # no computa el agarre bajo del peso muerto. Sumando lo declarado: 8 -> 0.
    assert prop.presupuestos["agarre"] == pytest.approx(0.0)
    # Tirón restringido: presupuesto de agarre crítico (C1 / I1).
    assert "tiron_vertical" in prop.patrones_restringidos
    # Bisagra prohibida hoy: swing ayer (D5, I2).
    assert prop.d5_activa
    assert "dominante_cadera" in prop.patrones_restringidos
    assert "D3" in prop.reglas_aplicadas

    # Sesión documentada en docs/06: válida con los mismos puntos.
    sesion = sesion_documentada(
        catalog,
        prop,
        [
            ("dead-bug", "B0"),
            ("agility-ladder-basic", "B0"),
            ("pushup-classic", "B1"),   # 3×12: empuje 0.5, core 0.5
            ("goblet-squat", "B1"),     # 3×10: rodilla 2, core 0.5
            ("pallof-press", "B2"),     # 3×10/lado: core 0.5
        ],
    )
    assert sesion.valida, sesion.violaciones
    assert sesion.puntos_sesion["empuje"] == 0.5
    assert sesion.puntos_sesion["rodilla_piernas"] == 2.0
    assert sesion.puntos_sesion["core"] == 1.5

    # Sustitución rechazada (docs/06): flexión por dominadas, agarre 2 > presupuesto.
    ok, motivos = check_substitution(
        catalog["pushup-classic"], catalog["pullup-strict"], prop, "A", catalog,
        puntos_actuales=sesion.puntos_sesion,
    )
    assert not ok
    assert any("agarre" in m for m in motivos)

    auto = generate(prop, estado, catalog, perfil.material)
    assert auto.valida, auto.violaciones
    for item in auto.items:
        ej = catalog[item.exercise_id]
        assert ej.impacto_lumbar == "verde"  # D3 / plantilla A
        assert ej.coste("agarre") in (None, "bajo")  # plantilla A


# --- Caso 3. Dolor lumbar al despertar -> D1 ----------------------------------------


def test_caso3_dolor_lumbar_d1(catalog, perfil):
    estado = DailyState(
        fecha=AHORA, recuperacion="amarillo", dolor=5, zona_dolor="lumbar",
        bjj_disponible="si", tipo_bjj="normal",
    )
    prop = decide(estado, [], catalog)
    assert prop.familia == "C"
    assert prop.descanso_opcion
    assert "D1" in prop.reglas_aplicadas
    assert "D1" in prop.explicacion
    assert "BJJ" in prop.explicacion  # recomendación sobre el BJJ de la tarde

    sesion = generate(prop, estado, catalog, perfil.material)
    assert sesion.valida, sesion.violaciones
    ids = [i.exercise_id for i in sesion.items]
    assert "treadmill-walk" in ids  # caminata en cinta
    assert "dead-bug" in ids
    for item in sesion.items:
        ej = catalog[item.exercise_id]
        assert all(c == "bajo" for c in ej.coste_dimensiones.values())  # plantilla C
        assert ej.impacto_lumbar == "verde"


# --- Caso 4. BJJ incierto -> familia A con margen (C5) --------------------------------


def test_caso4_bjj_incierto_c5(catalog, perfil):
    historial = [BjjRecord(AHORA - timedelta(hours=30), "duro")]  # ×0.6
    estado = DailyState(fecha=AHORA, recuperacion="verde", dolor=0, bjj_disponible="incierto")
    prop = decide(estado, historial, catalog)

    assert prop.familia == "A"
    assert prop.bjj_efectivo == "normal"
    assert "C5" in prop.reglas_aplicadas
    assert any("incierto" in i for i in prop.incertidumbres)
    # Carga activa ×0.6: todo baja (agarre 1.8, core 1.8, cardio 1.8, lumbar 1.2,
    # impacto 1.2, bisagra 0.6).
    assert prop.carga.puntos["agarre"] == pytest.approx(1.8)
    assert prop.carga.total != "alta"
    # Presupuestos ×0.5 (docs/13).
    assert prop.presupuestos["agarre"] == pytest.approx(3.1)
    assert prop.presupuestos["core"] == pytest.approx(3.1)
    assert prop.presupuestos["cardio"] == pytest.approx(3.1)
    assert prop.presupuestos["lumbar"] == pytest.approx(3.4)
    assert prop.presupuestos["empuje"] == pytest.approx(4.0)
    assert prop.presupuestos["rodilla_piernas"] == pytest.approx(4.0)
    assert prop.presupuestos["bisagra"] == pytest.approx(3.7)

    # Sesión documentada: válida.
    sesion = sesion_documentada(
        catalog,
        prop,
        [
            ("pushup-classic", "B1"),        # 3×12: empuje 0.5, core 0.5
            ("bulgarian-squat-trx", "B1"),   # 3×8/lado: rodilla 2, agarre 0.5
            ("plank-front", "B2"),           # 2×30 s: core 0.5
        ],
    )
    assert sesion.valida, sesion.violaciones
    assert sesion.puntos_sesion["agarre"] == 0.5
    assert sesion.puntos_sesion["rodilla_piernas"] == 2.0
    assert sesion.puntos_sesion["core"] == 1.0

    auto = generate(prop, estado, catalog, perfil.material)
    assert auto.valida, auto.violaciones


# --- Caso 5. Día rojo con motivación alta -> D2 -----------------------------------------


def test_caso5_dia_rojo_motivacion_d2(catalog, perfil):
    estado = DailyState(
        fecha=AHORA, recuperacion="rojo", dolor=0, bjj_disponible="no",
        preferencia="fuerza", circunstancias="5 h de sueño, fatiga alta",
    )
    prop = decide(estado, [], catalog)
    assert prop.familia == "C"
    assert prop.descanso_opcion
    assert "D2" in prop.reglas_aplicadas
    assert "D2" in prop.explicacion
    assert "Preferencia registrada" in prop.explicacion  # la motivación no anula

    sesion = generate(prop, estado, catalog, perfil.material)
    assert sesion.valida, sesion.violaciones
    assert all(i.bloque in ("B0", "continuo", "B2") for i in sesion.items)  # sin B1


# --- Caso 6. Día después de doble sesión -> A reducida (C4, C3, D5) ---------------------


def test_caso6_tras_doble_sesion_a_reducida(catalog, perfil):
    # Historial (ayer, ×1.0): la sesión B del caso 1 + BJJ duro. Los puntos
    # registrados son los de la sesión propuesta (docs/06): press militar core 0.5.
    ejercicios_caso1 = [
        ("kb-swing-two-hand", {"bisagra": 3.0, "lumbar": 2.0, "agarre": 2.0, "cardio": 2.0}),
        ("kb-press", {"empuje": 2.0, "core": 0.5}),
        ("pullup-strict", {"tiron": 2.0, "agarre": 2.0}),
        ("side-plank", {"core": 1.0}),
        ("rope-technical", {"cardio": 1.0, "impacto_articular": 1.0}),
    ]
    # Coherencia: los puntos registrados coinciden con puntos_propuesta en familia B.
    for eid, pts in ejercicios_caso1:
        assert puntos_propuesta(catalog[eid], "B", False) == pts

    historial = [
        PerformedSession(
            AHORA - timedelta(hours=23),
            [PerformedExercise(eid, puntos=pts) for eid, pts in ejercicios_caso1],
            familia="B",
        ),
        BjjRecord(AHORA - timedelta(hours=14), "duro"),
    ]
    estado = DailyState(fecha=AHORA, recuperacion="verde", dolor=0, bjj_disponible="no")
    prop = decide(estado, historial, catalog)

    # Carga activa exacta (docs/13): 5 dimensiones en media -> total alta.
    assert prop.carga.puntos["agarre"] == pytest.approx(7.0)
    assert prop.carga.puntos["cardio"] == pytest.approx(6.0)
    assert prop.carga.puntos["core"] == pytest.approx(4.5)
    assert prop.carga.puntos["lumbar"] == pytest.approx(4.0)
    assert prop.carga.puntos["bisagra"] == pytest.approx(4.0)
    assert prop.carga.total == "alta"

    assert prop.familia == "A"
    assert prop.reducida
    for regla in ("C3", "C4", "D5"):
        assert regla in prop.reglas_aplicadas

    # Presupuestos ×0.5 (docs/13).
    assert prop.presupuestos["agarre"] == pytest.approx(0.5)
    assert prop.presupuestos["cardio"] == pytest.approx(1.0)
    assert prop.presupuestos["core"] == pytest.approx(1.75)
    assert prop.presupuestos["lumbar"] == pytest.approx(2.0)
    assert prop.presupuestos["bisagra"] == pytest.approx(2.0)
    assert prop.presupuestos["empuje"] == pytest.approx(3.0)
    assert prop.presupuestos["rodilla_piernas"] == pytest.approx(4.0)
    assert prop.presupuestos["tiron"] == pytest.approx(3.0)

    # Sesión documentada: válida, core 1.5 ≤ 1.75, agarre 0.
    sesion = sesion_documentada(
        catalog,
        prop,
        [
            ("pike-pushup", "B1"),     # 3×8: empuje 2, core 0.5
            ("goblet-squat", "B1"),    # 3×10: rodilla 2, core 0.5
            ("side-plank", "B2"),      # 2×25 s: core 0.5
        ],
    )
    assert sesion.valida, sesion.violaciones
    assert sesion.puntos_sesion["core"] == 1.5
    assert sesion.puntos_sesion.get("agarre", 0.0) == 0.0

    auto = generate(prop, estado, catalog, perfil.material)
    assert auto.valida, auto.violaciones
    # D5: sin bisagra; plantilla A: sin agarre medio/alto.
    assert all(catalog[i.exercise_id].patron != "dominante_cadera" for i in auto.items)
    assert all(catalog[i.exercise_id].coste("agarre") in (None, "bajo") for i in auto.items)


# --- Caso 7. Día sin registro -> asunción conservadora declarada -----------------------


def test_caso7_dia_sin_registro_estimado(catalog, perfil):
    anteayer = (AHORA - timedelta(days=2)).date()  # sábado; BJJ asumido a las 19:00 -> ×0.6
    estado = DailyState(fecha=AHORA, recuperacion="verde", dolor=0, bjj_disponible="no")
    prop = decide(estado, [], catalog, dias_sin_registro=[anteayer])

    # Se asume BJJ normal estimado (docs/12): ×0.6.
    assert prop.carga.puntos["agarre"] == pytest.approx(1.2)
    assert prop.carga.puntos["core"] == pytest.approx(1.2)
    assert prop.carga.puntos["cardio"] == pytest.approx(1.2)
    assert prop.carga.puntos["lumbar"] == pytest.approx(0.6)
    assert prop.carga.puntos["impacto_articular"] == pytest.approx(0.6)
    assert prop.carga.puntos["bisagra"] == pytest.approx(0.6)
    # Presupuestos ligeramente reducidos (sin ×0.5: día sin BJJ -> familia B).
    assert prop.familia == "B"
    assert prop.presupuestos["agarre"] == pytest.approx(6.8)
    assert prop.presupuestos["core"] == pytest.approx(6.8)
    assert prop.presupuestos["cardio"] == pytest.approx(6.8)
    # Incertidumbre declarada en la explicación (D6).
    assert "D6" in prop.reglas_aplicadas
    assert any("sin registro" in i and "estimado" in i for i in prop.incertidumbres)
    assert "recalculo" in prop.explicacion


# --- Caso 8. Semana simulada completa -----------------------------------------------------


def _registrar_sesion(historial, sesion, fecha, familia):
    """Registra la sesión propuesta como realizada: computan los puntos de la
    propuesta; B0/B4 y las sesiones de recuperación no son estímulo (P1)."""
    cuenta_estimulo = familia != "C"
    items = [
        PerformedExercise(
            i.exercise_id,
            puntos=dict(i.puntos),
            cuenta_estimulo=cuenta_estimulo and i.bloque not in ("B0", "B4"),
        )
        for i in sesion.items
    ]
    historial.append(
        PerformedSession(fecha.replace(hour=10, minute=0), items, familia=familia)
    )


def test_caso8_semana_completa(catalog, perfil):
    """Semana tipo: BJJ lunes, miércoles (duro) y viernes. Se decide y se genera
    día a día con el historial acumulado, y se registra lo propuesto."""
    lunes = datetime(2026, 7, 27, 9, 0)
    dias = {
        "lun": (lunes, DailyState(fecha=lunes, recuperacion="verde", dolor=0, bjj_disponible="si", tipo_bjj="normal"), "A", "normal"),
        "mar": (lunes + timedelta(days=1), DailyState(fecha=lunes + timedelta(days=1), recuperacion="verde", dolor=0, bjj_disponible="no", preferencia="fuerza"), "B", None),
        "mie": (lunes + timedelta(days=2), DailyState(fecha=lunes + timedelta(days=2), recuperacion="verde", dolor=0, bjj_disponible="si", tipo_bjj="duro"), "A", "duro"),
        "jue": (lunes + timedelta(days=3), DailyState(fecha=lunes + timedelta(days=3), recuperacion="amarillo", dolor=0, bjj_disponible="no"), "C", None),
        "vie": (lunes + timedelta(days=4), DailyState(fecha=lunes + timedelta(days=4), recuperacion="verde", dolor=0, bjj_disponible="si", tipo_bjj="normal"), "A", "normal"),
        # El objetivo del día es técnico (matriz de docs/03: D puede sustituir a A/B);
        # P1 detecta la agilidad > 7 días sin estímulo.
        "sab": (lunes + timedelta(days=5), DailyState(fecha=lunes + timedelta(days=5), recuperacion="verde", dolor=0, bjj_disponible="no", preferencia="tecnica"), "D", None),
    }
    historial: list = []
    props = {}
    for nombre, (fecha, estado, familia_esperada, bjj) in dias.items():
        prop = decide(estado, historial, catalog)
        sesion = generate(prop, estado, catalog, perfil.material)
        assert sesion.valida, f"{nombre}: {sesion.violaciones}"
        assert prop.familia == familia_esperada, f"{nombre}: {prop.familia} != {familia_esperada}\n{prop.explicacion}"
        props[nombre] = prop
        _registrar_sesion(historial, sesion, fecha, prop.familia)
        if bjj:
            historial.append(BjjRecord(fecha.replace(hour=19, minute=0), bjj))

    # Miércoles: A reducida, sin bisagra (D5 por el swing del martes) ni lumbar (D3).
    assert props["mie"].reducida
    assert props["mie"].d5_activa
    assert props["mie"].d3_activa
    # Jueves: el valor del sistema — amarillo tras doble estímulo -> C (C3, C4).
    assert props["jue"].familia == "C"
    assert "C4" in props["jue"].reglas_aplicadas
    assert "C3" in props["jue"].reglas_aplicadas
    # Sábado: P1 detecta la agilidad > 7 días sin estímulo y la prioriza.
    assert "agilidad" in props["sab"].patrones_prioritarios
    assert "P1" in props["sab"].reglas_aplicadas


# --- Caso 9. Propuestas rechazadas o modificadas -----------------------------------------


def test_caso9a_dominada_rechazada_por_agarre(catalog):
    """9a: dominadas con presupuesto de agarre 0.5 -> rechazada; se ofrece un
    sustituto con agarre bajo (docs/06 ofrece remo TRX; cualquier sustituto
    válido del patrón con agarre ≤ 0.5 cumple la regla)."""
    # Historial con la aritmética exacta de docs/12: agarre 7 -> presupuesto 0.5
    # (swing a una mano 3 + remo 2 + BJJ normal 2).
    historial = [
        PerformedSession(
            AHORA - timedelta(hours=20),
            [PerformedExercise("kb-swing-one-hand"), PerformedExercise("kb-row-supported")],
        ),
        BjjRecord(AHORA - timedelta(hours=14), "normal"),
    ]
    estado = DailyState(fecha=AHORA, recuperacion="verde", dolor=0, bjj_disponible="si", tipo_bjj="normal")
    prop = decide(estado, historial, catalog)
    assert prop.presupuestos["agarre"] == pytest.approx(0.5)

    ok, motivos = check_substitution(
        catalog["pushup-classic"], catalog["pullup-strict"], prop, "A", catalog
    )
    assert not ok
    assert any("agarre" in m for m in motivos)

    # El remo TRX encaja: agarre 0.5 con dosis baja (aritmética literal de docs/06).
    assert puntos_propuesta(catalog["trx-row"], "A", True)["agarre"] == 0.5

    # El buscador ofrece un sustituto del mismo patrón con agarre bajo.
    sustituto = find_substitute(catalog["pullup-strict"], prop, "A", catalog)
    assert sustituto is not None
    assert puntos_propuesta(sustituto, "A", True)["agarre"] <= 0.5


def test_caso9b_swings_rechazados_antes_de_bjj_duro(catalog):
    """9b: añadir swings a una familia A antes de BJJ duro -> rechazado por D3
    (impacto lumbar amarillo); se ofrece press militar KB como estímulo compatible."""
    estado = DailyState(fecha=AHORA, recuperacion="verde", dolor=0, bjj_disponible="si", tipo_bjj="duro")
    prop = decide(estado, [], catalog)
    assert prop.familia == "A"
    assert prop.d3_activa and prop.d4_activa

    motivos = motivos_exclusion(catalog["kb-swing-two-hand"], prop, "A")
    assert any("D3" in m for m in motivos)
    assert motivos_exclusion(catalog["kb-press"], prop, "A") == []  # alternativa válida


def test_caso9c_dominada_sustituida_por_regresion(catalog):
    """9c: fatiga de agarre tras BJJ -> la dominada estricta se sustituye por la
    dominada asistida con goma (regresión documentada), manteniendo patrón y objetivo."""
    historial = [BjjRecord(AHORA - timedelta(hours=14), "duro", fatiga_agarre=True)]  # agarre 4
    estado = DailyState(fecha=AHORA, recuperacion="verde", dolor=0, bjj_disponible="no")
    prop = decide(estado, historial, catalog)

    ok, motivos = check_substitution(
        catalog["pullup-strict"], catalog["pullup-band-assisted"], prop, "B", catalog
    )
    assert ok, motivos
    # Mismo patrón, misma o menor carga de agarre.
    assert catalog["pullup-band-assisted"].patron == catalog["pullup-strict"].patron
    assert (
        puntos_propuesta(catalog["pullup-band-assisted"], "B", False)["agarre"]
        < puntos_propuesta(catalog["pullup-strict"], "B", False)["agarre"]
    )


# --- Caso 10. Intento de bisagra dos días seguidos -> D5 ----------------------------------


def test_caso10_bisagra_dos_dias_seguidos_d5(catalog, perfil):
    historial = [
        PerformedSession(
            AHORA - timedelta(hours=20),
            [
                PerformedExercise("kb-swing-two-hand"),   # bisagra exigente (coste alto)
                PerformedExercise("pike-pushup"),
                PerformedExercise("pullup-strict"),
                PerformedExercise("side-plank"),
            ],
            familia="B",
        )
    ]
    estado = DailyState(
        fecha=AHORA, recuperacion="verde", dolor=0, bjj_disponible="no", preferencia="fuerza"
    )
    prop = decide(estado, historial, catalog)
    assert prop.d5_activa
    assert "D5" in prop.reglas_aplicadas
    # Interpretación conservadora (docs/13 caso 10: "en la práctica se desaconseja"):
    # el patrón dominante_cadera queda restringido hoy, no solo los costes altos.
    assert "dominante_cadera" in prop.patrones_restringidos
    assert motivos_exclusion(catalog["kb-deadlift"], prop, prop.familia)

    sesion = generate(prop, estado, catalog, perfil.material)
    assert sesion.valida, sesion.violaciones
    # Sin bisagra hoy; se ofrece trabajo de pierna y empuje (docs/13).
    assert all(catalog[i.exercise_id].patron != "dominante_cadera" for i in sesion.items)
    patrones = {catalog[i.exercise_id].patron for i in sesion.items if i.bloque == "B1"}
    assert patrones & {"dominante_rodilla", "empuje_horizontal", "empuje_vertical"}


# --- Regla 9: filtro de material (modo sin material) --------------------------------------


def test_modo_sin_material_patron_pendiente(catalog, perfil):
    """Material vacío (viaje): solo entran ejercicios `sin_material` o de tatami;
    el tirón queda sin ejercicios disponibles y se declara patrón pendiente."""
    estado = DailyState(
        fecha=AHORA, recuperacion="verde", dolor=0, bjj_disponible="no",
        material_disponible=frozenset(),
    )
    prop = decide(estado, [], catalog)
    sesion = generate(prop, estado, catalog, perfil.material)
    assert sesion.valida, sesion.violaciones
    for item in sesion.items:
        ej = catalog[item.exercise_id]
        assert ej.sin_material or all(m == "tatami" for m in ej.material)
    texto = " ".join(sesion.notas)
    assert "tiron_horizontal" in texto and "pendiente" in texto
    assert "tiron_vertical" in texto
    # Aun así sale una sesión completa sin material.
    assert any(i.exercise_id == "pushup-classic" for i in sesion.items)
