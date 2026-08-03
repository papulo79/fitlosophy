"""Modelo de carga e inferencia (docs/12).

Calcula la carga activa por dimensión a partir del historial: decaimiento,
puntuación provisional, carga estimada del BJJ, acumulación y niveles.
Todos los valores numéricos son provisionales (se calibran en la Fase 9).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .catalog import DIMENSIONES, PUNTOS_COSTE, Catalog, Exercise
from .models import BjjRecord, Event, LoadVector, PerformedSession

# --- Valores provisionales (docs/12) -----------------------------------------
UMBRAL_MEDIA = 4.0  # < 4 puntos = baja
UMBRAL_ALTA = 8.0  # 4-8 = media (el límite pertenece al nivel inferior: 8 = media)
PRESUPUESTO_CRITICO = 0.5  # presupuesto < 0.5 -> dimensión restringida (I1, docs/13)
BJJ_DURACION_REFERENCIA = 75  # minutos
BJJ_DURACION_MUY_SUPERIOR = 90  # interpretación conservadora de "muy superior a la referencia"

# Carga estimada del BJJ por clasificación (tabla de docs/12).
BJJ_CARGA = {
    "tecnico": {"agarre": 1, "core": 1, "cardio": 1, "lumbar": 0, "impacto_articular": 0, "bisagra": 0},
    "normal": {"agarre": 2, "core": 2, "cardio": 2, "lumbar": 1, "impacto_articular": 1, "bisagra": 1},
    "duro": {"agarre": 3, "core": 3, "cardio": 3, "lumbar": 2, "impacto_articular": 2, "bisagra": 1},
}


def factor_decaimiento(horas: float) -> float:
    """Ventanas temporales de docs/12: 24 h ×1.0, 48 h ×0.6, 72 h ×0.3, > 72 h 0.

    El límite pertenece a la ventana inferior (24 h exactas = ×1.0), coherente
    con la regla de umbrales de docs/12 y con los ejemplos de docs/13.
    """
    if horas < 0:
        return 0.0  # evento futuro: no computa
    if horas <= 24:
        return 1.0
    if horas <= 48:
        return 0.6
    if horas <= 72:
        return 0.3
    return 0.0


def nivel_dimension(puntos: float) -> str:
    """Umbrales por dimensión (docs/12); el valor en el límite va al nivel inferior."""
    if puntos < UMBRAL_MEDIA:
        return "baja"
    if puntos <= UMBRAL_ALTA:
        return "media"
    return "alta"


def puntos_registro(ejercicio: Exercise) -> dict[str, float]:
    """Puntos de un ejercicio registrado con dosis neutra (docs/12).

    - Coste base por dimensión: bajo=1, medio=2, alto=3.
    - Patrón secundario: la mitad de puntos en las dimensiones que alimenta.
      Interpretación (ambigua en docs/12): la mitad de los puntos del ejercicio
      (su coste máximo por dimensión), no la mitad del coste declarado en esa
      dimensión. Es la lectura que reproduce los ejemplos de docs/12:
      swing a una mano (coste alto) -> core 1.5; remo (coste medio) -> core 1.
      En el catálogo actual coincide con (puntos+1)/2 en todos los casos.
    """
    pts = {d: PUNTOS_COSTE[c] for d, c in ejercicio.coste_dimensiones.items()}
    if ejercicio.secundarios and pts:
        maximo = max(pts.values())
        for dim in ejercicio.dimensiones_secundarias():
            pts[dim] = maximo / 2
    return pts


def bjj_puntos(registro: BjjRecord) -> dict[str, float]:
    """Carga estimada del BJJ (docs/12): tabla + ajustes de duración y agarre."""
    base = BJJ_CARGA[registro.clasificacion]
    pts = {d: float(p) for d, p in base.items() if p > 0}
    if registro.duracion_minutos > BJJ_DURACION_MUY_SUPERIOR:
        pts = {d: p * 1.25 for d, p in pts.items()}
    if registro.fatiga_agarre:
        pts["agarre"] = pts.get("agarre", 0.0) + 1.0
    return pts


def puntos_sesion_realizada(sesion: PerformedSession, catalog: Catalog) -> dict[str, float]:
    """Puntos de una sesión física registrada.

    Multiplicadores de dosis de docs/12. Una sesión de recuperación (patrón
    `recuperacion`) no suma carga en ninguna dimensión (regla de acumulación 4).
    """
    totales: dict[str, float] = {}
    for pe in sesion.ejercicios:
        ejercicio = catalog.get(pe.exercise_id)
        if ejercicio is None:
            continue
        if ejercicio.patron == "recuperacion":
            continue
        pts = dict(pe.puntos) if pe.puntos is not None else puntos_registro(ejercicio)
        mult = 1.0
        if pe.volumen_sobre_rango:
            mult *= 1.25
        if pe.al_fallo or (pe.rpe_real is not None and pe.rpe_real >= 9):
            mult *= 1.25
        if pe.rpe_real is not None and pe.rpe_real <= 5:
            mult *= 0.75
        if pe.fatiga_previa_alta:
            mult *= 1.25
        for d, p in pts.items():
            totales[d] = totales.get(d, 0.0) + p * mult
    return totales


def _descripcion_evento(evento: Event, catalog: Catalog) -> str:
    if isinstance(evento, BjjRecord):
        desc = f"BJJ {evento.clasificacion}"
        if evento.estimado:
            desc += " (estimado)"
        return desc
    nombres = [catalog[i.exercise_id].nombre for i in evento.ejercicios if catalog.get(i.exercise_id)]
    return "sesión física (" + ", ".join(nombres) + ")"


def compute_load(historial: list[Event], catalog: Catalog, ahora: datetime) -> LoadVector:
    """Carga activa por dimensión en el momento de decidir (docs/12).

    Reglas de acumulación:
    1. Suma de puntos decaídos de todas las sesiones (físicas y BJJ) en 72 h.
    2. Doble sesión que deja una dimensión en alta -> día siguiente conservador
       en esa dimensión aunque los puntos decaigan (nivel mínimo `media`).
    3. `total` = alta si hay 2+ dimensiones altas o 3+ medias.
    4. Recuperación no suma (aplicada en `puntos_sesion_realizada`).
    """
    puntos = {d: 0.0 for d in DIMENSIONES}
    origenes: dict[str, list[str]] = {d: [] for d in DIMENSIONES}
    incertidumbres: list[str] = []

    for evento in historial:
        horas = (ahora - evento.fecha).total_seconds() / 3600
        factor = factor_decaimiento(horas)
        if factor == 0.0:
            continue
        if isinstance(evento, BjjRecord):
            pts = bjj_puntos(evento)
            if evento.estimado:
                incertidumbres.append(
                    f"BJJ {evento.clasificacion} del {evento.fecha:%d/%m} asumido por falta de registro (estimado)."
                )
        else:
            pts = puntos_sesion_realizada(evento, catalog)
        if not pts:
            continue
        desc = _descripcion_evento(evento, catalog)
        for d, p in pts.items():
            puntos[d] = puntos.get(d, 0.0) + p * factor
            origenes.setdefault(d, []).append(f"{desc} (×{factor:g})")

    niveles = {d: nivel_dimension(p) for d, p in puntos.items()}

    # Regla 2: doble sesión del día anterior que dejó una dimensión en alta.
    conservadoras = _dimensiones_conservadoras(historial, catalog, ahora)
    for d in conservadoras:
        if niveles[d] == "baja":
            niveles[d] = "media"

    n_altas = sum(1 for n in niveles.values() if n == "alta")
    n_medias = sum(1 for n in niveles.values() if n == "media")
    total = "alta" if (n_altas >= 2 or n_medias >= 3) else ("media" if n_altas == 1 or n_medias >= 1 else "baja")

    # I1 (docs/13): presupuesto (umbral alto − carga) < 0.5 -> restringida aunque sea media.
    restringidas = [
        d for d in DIMENSIONES if niveles[d] != "alta" and (UMBRAL_ALTA - puntos[d]) < PRESUPUESTO_CRITICO
    ]

    return LoadVector(
        puntos=puntos,
        niveles=niveles,
        total=total,
        restringidas=restringidas,
        conservadoras=conservadoras,
        origenes=origenes,
        incertidumbres=incertidumbres,
    )


def _dimensiones_conservadoras(historial: list[Event], catalog: Catalog, ahora: datetime) -> list[str]:
    """Regla de acumulación 2: si dos sesiones del día anterior dejaron una
    dimensión en nivel alto, hoy se trata como conservadora en esa dimensión."""
    ayer = (ahora - timedelta(days=1)).date()
    eventos_ayer = [e for e in historial if e.fecha.date() == ayer]
    if len(eventos_ayer) < 2:
        return []
    suma: dict[str, float] = {}
    for evento in eventos_ayer:
        pts = bjj_puntos(evento) if isinstance(evento, BjjRecord) else puntos_sesion_realizada(evento, catalog)
        for d, p in pts.items():
            suma[d] = suma.get(d, 0.0) + p
    return [d for d, p in suma.items() if nivel_dimension(p) == "alta"]


def resumen_ayer(historial: list[Event], catalog: Catalog, ahora: datetime) -> dict:
    """Hechos del día anterior relevantes para las reglas del motor (docs/03).

    - `bjj_duro`: C4 y D4.
    - `doble_sesion_exigente`: C4. Interpretación (ambigua en docs/03): física +
      BJJ el mismo día solo cuenta si fue exigente (BJJ duro o sesión física con
      algún coste alto). Si cualquier física+BJJ contara, la semana tipo de
      docs/13 (caso 8) no produciría familia B el martes.
    - `bisagra_exigente`: D5 (I2, docs/13): ejercicio con coste de bisagra alto
      ese día, o carga de bisagra del día de nivel media o superior.
    """
    ayer = (ahora - timedelta(days=1)).date()
    eventos = [e for e in historial if e.fecha.date() == ayer]
    sesiones = [e for e in eventos if isinstance(e, PerformedSession)]
    bjj = [e for e in eventos if isinstance(e, BjjRecord)]

    bisagra_dia = 0.0
    bisagra_alto = False
    for sesion in sesiones:
        for pe in sesion.ejercicios:
            ejercicio = catalog.get(pe.exercise_id)
            if ejercicio is None:
                continue
            if ejercicio.coste("bisagra") == "alto":
                bisagra_alto = True
        bisagra_dia += puntos_sesion_realizada(sesion, catalog).get("bisagra", 0.0)
    for rec in bjj:
        bisagra_dia += bjj_puntos(rec).get("bisagra", 0.0)

    fisica_exigente = any(
        any(
            catalog.get(pe.exercise_id) is not None
            and "alto" in catalog[pe.exercise_id].coste_dimensiones.values()
            for pe in s.ejercicios
        )
        for s in sesiones
    )

    return {
        "hubo_sesion_fisica": bool(sesiones),
        "bjj_duro": any(r.clasificacion == "duro" for r in bjj),
        "doble_sesion_exigente": bool(sesiones and bjj and (fisica_exigente or any(r.clasificacion == "duro" for r in bjj))),
        "bisagra_exigente": bisagra_alto or nivel_dimension(bisagra_dia) in ("media", "alta"),
    }


def ultimo_estimulo_por_patron(historial: list[Event], catalog: Catalog) -> dict[str, datetime]:
    """Último estímulo registrado de cada patrón (principal y secundarios).

    Solo cuentan ejercicios con `cuenta_estimulo` (B0/B4 y dosis de
    recuperación no son estímulo, docs/06 regla 8). El BJJ no se mapea a
    patrones: su carga es estimada por dimensión (docs/12).
    """
    ultimo: dict[str, datetime] = {}
    for evento in historial:
        if not isinstance(evento, PerformedSession):
            continue
        for pe in evento.ejercicios:
            if not pe.cuenta_estimulo:
                continue
            ejercicio = catalog.get(pe.exercise_id)
            if ejercicio is None:
                continue
            for patron in (ejercicio.patron, *ejercicio.secundarios):
                if patron not in ultimo or evento.fecha > ultimo[patron]:
                    ultimo[patron] = evento.fecha
    return ultimo
