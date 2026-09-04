"""Tests de la regla de variedad (regla 10 de docs/06).

La recencia es el primer criterio de selección entre los candidatos que
superan los filtros duros: nunca usado primero, más días sin usarse después,
y un uso en las últimas 24 h manda al ejercicio al final de la cola. Las
claves de preferencia clásicas (nivel, explosividad...) desempatan. Sin
historial el resultado es idéntico al de siempre.
"""

from datetime import datetime, timedelta

import pytest

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
from fitlosophy.load import ultimo_uso_por_ejercicio

AHORA = datetime(2026, 8, 3, 9, 0)  # lunes


@pytest.fixture(scope="module")
def catalog():
    return load_default_catalog()


@pytest.fixture(scope="module")
def perfil():
    return load_default_perfil()


def _estado():
    return DailyState(
        fecha=AHORA, recuperacion="verde", dolor=0, bjj_disponible="no", preferencia="fuerza"
    )


def _prop(familia: str, prioritarios: list[str]) -> Proposal:
    """Propuesta mínima con presupuestos holgados para aislar la selección."""
    return Proposal(
        fecha=AHORA,
        familia=familia,
        presupuestos={d: 8.0 for d in DIMENSIONES},
        patrones_prioritarios=prioritarios,
    )


def test_ultimo_uso_cuenta_tambien_b0(catalog):
    ayer = AHORA - timedelta(days=1)
    historial = [
        PerformedSession(
            ayer,
            [
                PerformedExercise("dead-bug", cuenta_estimulo=False),  # B0
                PerformedExercise("goblet-squat"),
            ],
        )
    ]
    ultimo = ultimo_uso_por_ejercicio(historial)
    assert ultimo["dead-bug"] == ayer
    assert ultimo["goblet-squat"] == ayer
    assert "kb-swing-two-hand" not in ultimo


def test_sin_historial_resultado_identico(catalog, perfil):
    prop = decide(_estado(), [], catalog)
    sin = generate(prop, _estado(), catalog, perfil.material)
    vacio = generate(prop, _estado(), catalog, perfil.material, [])
    assert [i.exercise_id for i in sin.items] == [i.exercise_id for i in vacio.items]


def test_historial_rota_la_sesion(catalog, perfil):
    estado = _estado()
    prop = decide(estado, [], catalog)
    primera = generate(prop, estado, catalog, perfil.material)
    ayer = AHORA - timedelta(days=1)
    historial = [
        PerformedSession(
            ayer,
            [
                PerformedExercise(item.exercise_id, cuenta_estimulo=item.bloque not in ("B0", "B4"))
                for item in primera.items
            ],
        )
    ]
    segunda = generate(prop, estado, catalog, perfil.material, historial)
    ids_primera = [i.exercise_id for i in primera.items]
    ids_segunda = [i.exercise_id for i in segunda.items]
    assert ids_segunda != ids_primera
    assert segunda.valida, segunda.violaciones
    # La justificación declara cuándo la recencia decidió el desempate.
    assert any("variedad:" in i.justificacion for i in segunda.items)


def test_b0_tambien_rota(catalog, perfil):
    estado = _estado()
    prop = decide(estado, [], catalog)
    ayer = AHORA - timedelta(days=1)
    historial = [
        PerformedSession(
            ayer,
            [
                PerformedExercise("dead-bug", cuenta_estimulo=False),
                PerformedExercise("agility-ladder-basic", cuenta_estimulo=False),
            ],
        )
    ]
    sesion = generate(prop, estado, catalog, perfil.material, historial)
    b0 = [i.exercise_id for i in sesion.items_bloque("B0")]
    assert len(b0) == 2
    assert "dead-bug" not in b0
    assert "agility-ladder-basic" not in b0


# --- Recencia como primer criterio (regla 10 revisada) ---------------------------


def test_recencia_gana_al_nivel_en_familia_a(catalog, perfil):
    """Un «base» usado ayer cede el slot a un «intermedio» nunca usado del
    mismo patrón (empuje_horizontal: pushup-classic -> pushup-feet-elevated)."""
    prop = _prop("A", ["empuje_horizontal"])
    control = generate(prop, _estado(), catalog, perfil.material)
    assert "pushup-classic" in [i.exercise_id for i in control.items_bloque("B1")]

    historial = [PerformedSession(AHORA - timedelta(days=1), [PerformedExercise("pushup-classic")])]
    sesion = generate(prop, _estado(), catalog, perfil.material, historial)
    b1 = [i.exercise_id for i in sesion.items_bloque("B1")]
    assert "pushup-classic" not in b1
    assert "pushup-feet-elevated" in b1
    assert sesion.valida, sesion.violaciones


def test_recencia_gana_a_explosividad_en_familia_b(catalog, perfil):
    """En B, un no explosivo nunca usado gana al explosivo usado hace 2 días;
    el orden de bloque (regla 4) sigue poniendo explosivos primero en B1."""
    prop = _prop("B", ["dominante_cadera"])
    hace_2 = AHORA - timedelta(days=2)
    historial = [
        PerformedSession(
            hace_2,
            [PerformedExercise("kb-swing-two-hand"), PerformedExercise("kb-swing-one-hand")],
        )
    ]
    sesion = generate(prop, _estado(), catalog, perfil.material, historial)
    b1 = [i.exercise_id for i in sesion.items_bloque("B1")]
    assert "kb-swing-two-hand" not in b1
    assert "kb-swing-one-hand" not in b1
    bisagra = next(eid for eid in b1 if catalog[eid].patron == "dominante_cadera")
    assert not catalog[bisagra].explosivo
    assert sesion.valida, sesion.violaciones

    # Sin historial el swing (explosivo) entra y _ordenar_bloques lo pone
    # primero en B1: la regla 4 es de ordenación de bloque, no de selección.
    control = generate(prop, _estado(), catalog, perfil.material)
    b1_control = control.items_bloque("B1")
    assert any(catalog[i.exercise_id].explosivo for i in b1_control)
    assert catalog[b1_control[0].exercise_id].explosivo


def test_usado_hoy_solo_si_no_hay_alternativa(catalog, perfil):
    """Usado hace <24 h: cede el slot si hay alternativa en el patrón; se
    elige solo cuando es el único candidato disponible."""
    prop = _prop("A", ["empuje_horizontal"])
    historial = [
        PerformedSession(AHORA - timedelta(hours=3), [PerformedExercise("pushup-classic")])
    ]
    sesion = generate(prop, _estado(), catalog, perfil.material, historial)
    b1 = [i.exercise_id for i in sesion.items_bloque("B1")]
    assert "pushup-classic" not in b1
    assert "pushup-feet-elevated" in b1

    # Sin alternativa en el patrón (treadmill-walk es el único de
    # `recuperacion`), el ejercicio usado hoy se elige igualmente.
    prop_c = _prop("C", [])
    historial_c = [
        PerformedSession(AHORA - timedelta(hours=3), [PerformedExercise("treadmill-walk")])
    ]
    sesion_c = generate(prop_c, _estado(), catalog, perfil.material, historial_c)
    assert "treadmill-walk" in [i.exercise_id for i in sesion_c.items]
    assert sesion_c.valida, sesion_c.violaciones
