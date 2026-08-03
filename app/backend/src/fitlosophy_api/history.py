"""Reconstrucción del historial del motor desde la persistencia.

La carga activa se calcula siempre desde el historial persistido (sesiones
realizadas finalizadas/cerradas + registros de BJJ), nunca desde datos de
prueba. Incluye el mapeo zona de molestia → dimensión de carga para la
congelación de ventana tras respuesta negativa (docs/12).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from fitlosophy.catalog import Catalog
from fitlosophy.models import BjjRecord, Event, PerformedExercise, PerformedSession

from .db import cargar_json

# Zona de molestia declarada en el cierre → dimensiones de carga afectadas
# (docs/12: la respuesta negativa mantiene la dimensión afectada 24 h más).
# Interpretación conservadora documentada: una zona desconocida no congela
# nada, pero se anota en el registro para revisión manual (Fase 9).
ZONA_DIMENSIONES: dict[str, list[str]] = {
    "lumbar": ["lumbar"],
    "zona_lumbar": ["lumbar"],
    "sacro": ["lumbar"],
    "espalda_baja": ["lumbar"],
    "cadera": ["bisagra"],
    "gluteo": ["bisagra"],
    "isquios": ["bisagra", "rodilla_piernas"],
    "isquiotibiales": ["bisagra", "rodilla_piernas"],
    "rodilla": ["rodilla_piernas"],
    "cuadriceps": ["rodilla_piernas"],
    "gemelo": ["rodilla_piernas", "impacto_articular"],
    "tobillo": ["impacto_articular"],
    "pie": ["impacto_articular"],
    "hombro": ["empuje"],
    "pecho": ["empuje"],
    "triceps": ["empuje"],
    "codo": ["empuje", "tiron"],
    "espalda": ["tiron"],
    "dorsal": ["tiron"],
    "antebrazo": ["agarre"],
    "mano": ["agarre"],
    "muneca": ["agarre"],
    "dedos": ["agarre"],
    "abdomen": ["core"],
    "core": ["core"],
    "cervical": ["core"],
    "cuello": ["core"],
}


def dimensiones_de_molestias(molestias: list[dict]) -> tuple[list[str], list[str]]:
    """Dimensiones afectadas por las molestias del cierre.

    Devuelve (dimensiones, zonas_desconocidas). Solo las molestias con
    intensidad > 0 congelan ventana.
    """
    dims: set[str] = set()
    desconocidas: list[str] = []
    for m in molestias:
        zona = (m.get("zona") or "").strip().lower()
        intensidad = m.get("intensidad", 0) or 0
        if not zona or intensidad <= 0:
            continue
        mapeo = ZONA_DIMENSIONES.get(zona)
        if mapeo is None:
            desconocidas.append(zona)
        else:
            dims.update(mapeo)
    return sorted(dims), desconocidas


def _item_a_performed(fila: sqlite3.Row, catalog: Catalog, rpe_real: int | None, familia: str | None) -> PerformedExercise | None:
    """Convierte un ítem persistido en el ejercicio realmente realizado.

    La dosis real sustituye a la prevista (criterio 4 de docs/14): se usan los
    puntos reales calculados al finalizar; los ítems no realizados no computan.
    """
    estado = fila["estado"]
    if estado == "no_realizado":
        return None
    exercise_id = fila["exercise_id_real"] or fila["exercise_id"]
    if catalog.get(exercise_id) is None:
        return None
    puntos = cargar_json(fila["puntos_reales"], None)
    if puntos is None:
        puntos = cargar_json(fila["puntos_previstos"], {})
    cuenta_estimulo = fila["bloque"] not in ("B0", "B4") and familia != "C"
    return PerformedExercise(
        exercise_id=exercise_id,
        puntos=puntos,
        rpe_real=rpe_real,
        cuenta_estimulo=cuenta_estimulo,
    )


def construir_historial(conn: sqlite3.Connection, catalog: Catalog) -> list[Event]:
    """Historial completo (sesiones físicas + BJJ) ordenado por fecha."""
    eventos: list[Event] = []

    sesiones = conn.execute(
        "SELECT * FROM training_sessions WHERE estado IN ('finalizada', 'cerrada') ORDER BY fecha"
    ).fetchall()
    for sesion in sesiones:
        items = conn.execute(
            "SELECT * FROM session_items WHERE session_id = ? ORDER BY id", (sesion["id"],)
        ).fetchall()
        ejercicios = [
            pe
            for pe in (_item_a_performed(i, catalog, sesion["rpe_real"], sesion["familia"]) for i in items)
            if pe is not None
        ]
        congeladas: tuple[str, ...] = ()
        cierre = conn.execute(
            "SELECT dimensiones_congeladas FROM session_closures WHERE session_id = ?", (sesion["id"],)
        ).fetchone()
        if cierre is not None:
            congeladas = tuple(cargar_json(cierre["dimensiones_congeladas"], []))
        eventos.append(
            PerformedSession(
                fecha=datetime.fromisoformat(sesion["fecha"]),
                ejercicios=ejercicios,
                familia=sesion["familia"],
                rpe_real=sesion["rpe_real"],
                congelar_dimensiones=congeladas,
            )
        )

    for rec in conn.execute("SELECT * FROM bjj_records ORDER BY fecha").fetchall():
        eventos.append(
            BjjRecord(
                fecha=datetime.fromisoformat(rec["fecha"]),
                clasificacion=rec["clasificacion"],
                duracion_minutos=rec["duracion_minutos"],
                fatiga_agarre=bool(rec["fatiga_agarre"]),
                estimado=bool(rec["estimado"]),
            )
        )

    eventos.sort(key=lambda e: e.fecha)
    return eventos
