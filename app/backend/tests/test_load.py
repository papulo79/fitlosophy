"""Tests del modelo de carga (docs/12): decaimiento, puntuación, BJJ estimado,
acumulación, niveles y tratamiento de datos incompletos."""

from datetime import datetime, timedelta

import pytest

from fitlosophy import (
    BjjRecord,
    PerformedExercise,
    PerformedSession,
    load_default_catalog,
)
from fitlosophy.load import (
    bjj_puntos,
    compute_load,
    factor_decaimiento,
    nivel_dimension,
    puntos_registro,
)

AHORA = datetime(2026, 8, 3, 9, 0)


@pytest.fixture(scope="module")
def catalog():
    return load_default_catalog()


# --- Decaimiento (docs/12) ------------------------------------------------------


@pytest.mark.parametrize(
    "horas,esperado",
    [
        (1, 1.0),
        (12, 1.0),
        (24, 1.0),   # el límite pertenece a la ventana inferior
        (25, 0.6),
        (47, 0.6),
        (48, 0.6),
        (49, 0.3),
        (60, 0.3),
        (72, 0.3),
        (73, 0.0),
        (100, 0.0),
    ],
)
def test_factor_decaimiento(horas, esperado):
    assert factor_decaimiento(horas) == esperado


# --- Umbrales de niveles (docs/12, I1 de docs/13) --------------------------------


@pytest.mark.parametrize(
    "puntos,esperado",
    [(0, "baja"), (3.9, "baja"), (4, "media"), (8, "media"), (8.1, "alta"), (12, "alta")],
)
def test_niveles_umbrales(puntos, esperado):
    assert nivel_dimension(puntos) == esperado


# --- Puntos por ejercicio ----------------------------------------------------------


def test_puntos_coste_base(catalog):
    # bajo=1, medio=2, alto=3 (docs/12).
    assert puntos_registro(catalog["kb-swing-two-hand"]) == {
        "bisagra": 3.0,
        "lumbar": 2.0,
        "agarre": 2.0,
        "cardio": 2.0,
    }


def test_patron_secundario_a_la_mitad(catalog):
    # Ejemplos literales de docs/12: el secundario computa la mitad de los
    # puntos del ejercicio (swing a una mano: core 1.5; remo: core 1).
    assert puntos_registro(catalog["kb-swing-one-hand"])["core"] == 1.5
    assert puntos_registro(catalog["kb-row-supported"])["core"] == 1.0


# --- Carga estimada del BJJ (tabla de docs/12) --------------------------------------


def test_bjj_tabla_tecnico_normal_duro():
    assert bjj_puntos(BjjRecord(AHORA, "tecnico")) == {"agarre": 1.0, "core": 1.0, "cardio": 1.0}
    assert bjj_puntos(BjjRecord(AHORA, "normal")) == {
        "agarre": 2.0, "core": 2.0, "cardio": 2.0, "lumbar": 1.0, "impacto_articular": 1.0, "bisagra": 1.0,
    }
    assert bjj_puntos(BjjRecord(AHORA, "duro")) == {
        "agarre": 3.0, "core": 3.0, "cardio": 3.0, "lumbar": 2.0, "impacto_articular": 2.0, "bisagra": 1.0,
    }


def test_bjj_ajustes_duracion_y_agarre():
    # Duración muy superior a la referencia (75 min) -> ×1.25; fatiga de agarre -> +1.
    pts = bjj_puntos(BjjRecord(AHORA, "normal", duracion_minutos=100))
    assert pts["agarre"] == 2.5 and pts["lumbar"] == 1.25
    pts = bjj_puntos(BjjRecord(AHORA, "duro", fatiga_agarre=True))
    assert pts["agarre"] == 4.0
    # 90 min no es "muy superior" (interpretación conservadora).
    assert bjj_puntos(BjjRecord(AHORA, "normal", duracion_minutos=90))["agarre"] == 2.0


# --- Ejemplo completo de docs/12 -----------------------------------------------------


def test_ejemplo_completo_docs12(catalog):
    """Historial de las últimas 24 h: swing a una mano + peso muerto + remo + BJJ normal."""
    historial = [
        PerformedSession(
            AHORA - timedelta(hours=20),
            [
                PerformedExercise("kb-swing-one-hand"),
                PerformedExercise("kb-deadlift"),
                PerformedExercise("kb-row-supported"),
            ],
        ),
        BjjRecord(AHORA - timedelta(hours=14), "normal"),
    ]
    carga = compute_load(historial, catalog, AHORA)
    assert carga.puntos["bisagra"] == 6.0
    assert carga.puntos["lumbar"] == 6.0
    assert carga.puntos["core"] == 4.5
    assert carga.puntos["tiron"] == 2.0
    assert carga.puntos["cardio"] == 2.0
    assert carga.puntos["impacto_articular"] == 1.0
    # Desviación documentada: docs/12 calcula agarre 7 porque no computa el
    # agarre bajo declarado del peso muerto (kb-deadlift: agarre bajo). Sumando
    # todo lo declarado (más conservador) son 8. El nivel es `media` en ambos.
    assert carga.puntos["agarre"] == 8.0
    for d in ("bisagra", "lumbar", "agarre", "core"):
        assert carga.niveles[d] == "media"
    # Cuatro dimensiones en media -> total alta (regla de docs/12).
    assert carga.total == "alta"


# --- Reglas de acumulación ------------------------------------------------------------


def test_total_dos_altas_o_tres_medias(catalog):
    def historial_con(puntos):
        return [
            PerformedSession(AHORA - timedelta(hours=5), [PerformedExercise("kb-swing-two-hand", puntos=puntos)])
        ]

    # 2 dimensiones altas -> total alta
    carga = compute_load(historial_con({"lumbar": 9.0, "agarre": 9.0}), catalog, AHORA)
    assert carga.total == "alta"
    # 3 medias -> total alta
    carga = compute_load(historial_con({"lumbar": 5.0, "agarre": 5.0, "core": 4.0}), catalog, AHORA)
    assert carga.total == "alta"
    # 2 medias -> total no alta
    carga = compute_load(historial_con({"lumbar": 5.0, "agarre": 5.0}), catalog, AHORA)
    assert carga.total != "alta"


def test_recuperacion_no_suma(catalog):
    historial = [
        PerformedSession(AHORA - timedelta(hours=3), [PerformedExercise("treadmill-walk")]),
    ]
    carga = compute_load(historial, catalog, AHORA)
    assert all(p == 0.0 for p in carga.puntos.values())


def test_presupuesto_critico_restringe_aunque_media(catalog):
    # I1 (docs/13): presupuesto (8 − carga) < 0.5 -> restringida aunque sea media.
    historial = [
        PerformedSession(AHORA - timedelta(hours=5), [PerformedExercise("kb-swing-two-hand", puntos={"agarre": 7.6})])
    ]
    carga = compute_load(historial, catalog, AHORA)
    assert carga.niveles["agarre"] == "media"
    assert "agarre" in carga.restringidas


def test_doble_sesion_con_dim_alta_deja_dia_siguiente_conservador(catalog):
    # Regla de acumulación 2: ayer doble sesión dejó agarre en alta; hoy, aunque
    # los puntos decaigan por debajo de media, la dimensión se trata conservadora.
    ayer = AHORA - timedelta(days=1)
    historial = [
        PerformedSession(ayer.replace(hour=10), [PerformedExercise("kb-swing-two-hand", puntos={"agarre": 5.0})]),
        BjjRecord(ayer.replace(hour=19), "duro", fatiga_agarre=True),  # 3+1 agarre
    ]
    # Decaimiento del día anterior (24-48 h, ×0.6): 9×0.6 = 5.4 -> media por puntos;
    # forzamos el escenario decaído comprobando el flag conservador.
    historial[0] = PerformedSession(
        ayer.replace(hour=10), [PerformedExercise("kb-swing-two-hand", puntos={"agarre": 5.4})]
    )
    carga = compute_load(historial, catalog, AHORA)
    assert "agarre" in carga.conservadoras
    assert carga.niveles["agarre"] in ("media", "alta")


def test_multiplicadores_de_dosis(catalog):
    # Volumen por encima del rango ×1.25; RPE ≤ 5 ×0.75 (docs/12).
    historial = [
        PerformedSession(
            AHORA - timedelta(hours=5),
            [PerformedExercise("pushup-classic", volumen_sobre_rango=True)],
        )
    ]
    carga = compute_load(historial, catalog, AHORA)
    assert carga.puntos["empuje"] == 1.25
    historial = [
        PerformedSession(AHORA - timedelta(hours=5), [PerformedExercise("pushup-classic", rpe_real=5)])
    ]
    carga = compute_load(historial, catalog, AHORA)
    assert carga.puntos["empuje"] == 0.75


def test_bjj_estimado_declara_incertidumbre(catalog):
    historial = [BjjRecord(AHORA - timedelta(hours=30), "normal", estimado=True)]
    carga = compute_load(historial, catalog, AHORA)
    assert carga.puntos["agarre"] == 1.2  # 2 × 0.6
    assert carga.incertidumbres
