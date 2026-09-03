"""Tests de la regla de variedad (regla 10 de docs/06).

El generador desempata entre candidatos equivalentes eligiendo el que lleva
más días sin usarse; sin historial el resultado es idéntico al de siempre.
"""

from datetime import datetime, timedelta

import pytest

from fitlosophy import (
    DailyState,
    PerformedExercise,
    PerformedSession,
    decide,
    generate,
    load_default_catalog,
    load_default_perfil,
)
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
