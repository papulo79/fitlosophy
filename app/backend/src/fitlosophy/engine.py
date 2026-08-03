"""Motor de decisión diario (docs/03).

Del estado diario + historial + biblioteca a: familia de sesión, techo de
intensidad, presupuesto por dimensión, patrones prioritarios y restringidos,
y una explicación en español con las reglas citadas.

Prioridad entre reglas: duras (D) > carga (C) > preferencia (P).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from .catalog import DIMENSIONES, PATRON_DIMENSIONES, Catalog
from .load import (
    UMBRAL_ALTA,
    compute_load,
    resumen_ayer,
    ultimo_estimulo_por_patron,
)
from .models import BjjRecord, DailyState, Event, Proposal

# --- Valores provisionales (docs/03) -----------------------------------------
DOLOR_RELEVANTE = 4  # D1
FACTOR_COMPATIBLE = 0.5  # paso 5: presupuesto en familia A
AUSENCIA_PATRON_DIAS = 7  # P1

# Techos de intensidad y su orden (interpretación del flujo de docs/03:
# `media` permite familia A reducida — caso 6 de docs/13 —; `compatible` es el
# techo del día amarillo; `recuperacion` solo permite familia C).
_RANGO_TECHO = {"recuperacion": 0, "compatible": 1, "media": 2, "potente": 3}

# Patrones permitidos por familia (plantillas de docs/06).
PATRONES_FAMILIA = {
    "A": {
        "empuje_horizontal",
        "empuje_vertical",
        "tiron_horizontal",
        "tiron_vertical",
        "dominante_rodilla",
        "core_antiextension",
        "core_antirotacion",
        "core_lateral",
        "acondicionamiento",
    },
    "B": set(PATRON_DIMENSIONES),
    "C": {
        "recuperacion",
        "movilidad_cargada",
        "core_antiextension",
        "core_antirotacion",
        "core_lateral",
        "dominante_cadera",
        "dominante_rodilla",
    },
    "D": {"agilidad", "acondicionamiento"},
}

_NOMBRE_FAMILIA = {
    "A": "físico compatible con BJJ",
    "B": "físico potente sin BJJ",
    "C": "recuperación activa",
    "D": "técnica y agilidad",
}


def _min_techo(a: str, b: str) -> str:
    return a if _RANGO_TECHO[a] <= _RANGO_TECHO[b] else b


def decide(
    estado: DailyState,
    historial: list[Event],
    catalog: Catalog,
    dias_sin_registro: list[date] | None = None,
) -> Proposal:
    """Flujo completo de docs/03 (8 pasos).

    `dias_sin_registro`: días dentro de la ventana de 72 h sin dato alguno.
    Si el patrón de uso sugiere que pudo haber sesión, se asume BJJ normal
    estimado (docs/12, datos incompletos; caso 7 de docs/13). Decisión
    conservadora: siempre se asume BJJ normal en el hueco.
    """
    ahora = estado.fecha
    reglas: list[str] = []
    incertidumbres: list[str] = []

    # --- Paso 1: carga activa (docs/12) ---------------------------------------
    historial_ampliado = list(historial)
    for dia in dias_sin_registro or []:
        if 0 <= (ahora.date() - dia).days <= 3:
            historial_ampliado.append(
                BjjRecord(
                    fecha=datetime.combine(dia, datetime.min.time()).replace(hour=19),
                    clasificacion="normal",
                    estimado=True,
                )
            )
            incertidumbres.append(
                f"{dia:%d/%m} sin registro: asumo BJJ normal por tu patrón habitual "
                "(estimado, confianza media). Si no entrenaste, dímelo y recalculo (D6)."
            )
            reglas.append("D6")
    carga = compute_load(historial_ampliado, catalog, ahora)
    incertidumbres.extend(carga.incertidumbres)

    ayer = resumen_ayer(historial_ampliado, catalog, ahora)

    # --- Paso 2: reglas duras D1, D2 -------------------------------------------
    if estado.dolor >= DOLOR_RELEVANTE or estado.limitacion:
        reglas.append("D1")
        motivo = (
            f"Dolor {estado.dolor}/10"
            + (f" en {estado.zona_dolor}" if estado.zona_dolor else "")
            if estado.dolor >= DOLOR_RELEVANTE
            else f"Limitación de movimiento ({estado.limitacion})"
        )
        return _propuesta_recuperacion(
            estado, carga, motivo, "D1", reglas, incertidumbres
        )
    if estado.recuperacion == "rojo":
        reglas.append("D2")
        return _propuesta_recuperacion(
            estado, carga, "Recuperación roja", "D2", reglas, incertidumbres
        )

    # --- Paso 3: techo de intensidad (reglas de carga) --------------------------
    techo = "potente"
    if carga.total == "alta":
        reglas.append("C3")
        if estado.recuperacion == "verde" and estado.dolor == 0:
            # C3: total alta -> C como máximo, salvo verde y sin dolor -> A reducida.
            techo = _min_techo(techo, "compatible")
        else:
            techo = _min_techo(techo, "recuperacion")
    if ayer["bjj_duro"] or ayer["doble_sesion_exigente"]:
        reglas.append("C4")
        techo = _min_techo(techo, "media")
    if estado.recuperacion == "amarillo":
        techo = _min_techo(techo, "compatible")

    # --- Paso 4: familia de sesión ----------------------------------------------
    bjj_efectivo: str | None = None
    if estado.bjj_disponible == "si":
        bjj_efectivo = estado.tipo_bjj or "normal"
        if estado.tipo_bjj is None:
            incertidumbres.append("Tipo de BJJ desconocido: se asume normal (decisión conservadora).")
    elif estado.bjj_disponible == "incierto":
        reglas.append("C5")
        bjj_efectivo = "normal"
        incertidumbres.append("BJJ incierto: se conserva margen como si hubiera BJJ normal (C5).")

    if bjj_efectivo:
        familia = "A" if _RANGO_TECHO[techo] >= _RANGO_TECHO["compatible"] else "C"
    else:
        if techo == "potente":
            familia = "B"  # C6: la ausencia de BJJ no obliga, pero recuperación y preferencia la avalan
            reglas.append("C6")
        elif techo in ("media", "compatible"):
            familia = "A"
        else:
            familia = "C"
        # P2: la preferencia declarada desempata entre opciones válidas.
        if estado.preferencia == "tecnica" and familia in ("A", "B"):
            reglas.append("P2")
            familia = "D"

    reducida = familia == "A" and (
        carga.total == "alta" or techo != "potente" or bjj_efectivo == "duro"
    )

    # --- Reglas duras sobre la selección preliminar (paso 7) ---------------------
    d3 = bool(bjj_efectivo in ("normal", "duro"))
    d4 = bool(bjj_efectivo == "duro")
    d5 = bool(ayer["bisagra_exigente"])
    if d3:
        reglas.append("D3")
    if d4:
        reglas.append("D4")
    if d5:
        reglas.append("D5")

    # --- Paso 5: presupuesto por dimensión ---------------------------------------
    factor = FACTOR_COMPATIBLE if (familia == "A" or (familia == "D" and bjj_efectivo)) else 1.0
    presupuestos = {
        d: max(UMBRAL_ALTA - carga.puntos[d], 0.0) * factor for d in DIMENSIONES
    }

    # --- Paso 6: patrones restringidos, dosificados y prioritarios ----------------
    restringidos: dict[str, str] = {}
    dims_alta = [d for d in DIMENSIONES if carga.niveles[d] == "alta"]
    dims_restringida = [d for d in carga.restringidas]
    for d in dims_alta:
        reglas.append("C1")
        for patron, dims in PATRON_DIMENSIONES.items():
            if d in dims:
                restringidos[patron] = f"C1: dimensión {d} en alta"
    for d in dims_restringida:
        for patron, dims in PATRON_DIMENSIONES.items():
            if d in dims and patron not in restringidos:
                restringidos[patron] = f"C1: presupuesto de {d} crítico (< 0.5 puntos)"
    if d5:
        # D5 (I2): ayer hubo bisagra exigente -> hoy prohibida la bisagra exigente.
        restringidos["dominante_cadera"] = "D5: bisagra exigente ayer; hoy prohibida"

    dosificados: list[str] = []
    for d in DIMENSIONES:
        if carga.niveles[d] == "media" and d not in dims_restringida:
            reglas.append("C2")
            for patron, dims in PATRON_DIMENSIONES.items():
                if d in dims and patron not in restringidos and patron not in dosificados:
                    dosificados.append(patron)

    ultimo = ultimo_estimulo_por_patron(historial_ampliado, catalog)
    prioritarios: list[str] = []
    for patron in catalog.patrones:
        if patron in restringidos or patron not in PATRONES_FAMILIA[familia]:
            continue
        ultima_fecha = ultimo.get(patron)
        dias = (ahora - ultima_fecha).days if ultima_fecha else None
        if ultima_fecha is None or dias > AUSENCIA_PATRON_DIAS:
            prioritarios.append(patron)
            reglas.append("P1")

    # --- Paso 8: explicación -------------------------------------------------------
    prop = Proposal(
        fecha=ahora,
        familia=familia,
        reducida=reducida,
        descanso_opcion=False,
        techo=techo,
        bjj_efectivo=bjj_efectivo,
        presupuestos=presupuestos,
        patrones_prioritarios=prioritarios,
        patrones_restringidos=restringidos,
        patrones_dosificados=dosificados,
        d3_activa=d3,
        d4_activa=d4,
        d5_activa=d5,
        reglas_aplicadas=sorted(set(reglas)),
        incertidumbres=incertidumbres,
        carga=carga,
    )
    prop.explicacion = _explicar(prop, estado, ayer)
    return prop


def _propuesta_recuperacion(
    estado: DailyState,
    carga,
    motivo: str,
    regla: str,
    reglas: list[str],
    incertidumbres: list[str],
) -> Proposal:
    """D1/D2: recuperación activa o descanso; la motivación no anula (D2)."""
    factor = 1.0
    presupuestos = {d: max(UMBRAL_ALTA - carga.puntos[d], 0.0) * factor for d in DIMENSIONES}
    prop = Proposal(
        fecha=estado.fecha,
        familia="C",
        reducida=False,
        descanso_opcion=True,
        techo="recuperacion",
        bjj_efectivo=(estado.tipo_bjj or "normal") if estado.bjj_disponible in ("si", "incierto") else None,
        presupuestos=presupuestos,
        reglas_aplicadas=sorted(set(reglas)),
        incertidumbres=incertidumbres,
        carga=carga,
    )
    partes = [f"{motivo}: regla dura {regla}. Solo recuperación activa o descanso."]
    if regla == "D2" and estado.preferencia:
        partes.append(
            "Preferencia registrada. La recuperación roja es una regla dura (D2): "
            "hoy no hay sesión de estímulo. Si mañana amanece en verde, la sesión "
            "potente tendrá prioridad de patrones frescos."
        )
    if estado.bjj_disponible in ("si", "incierto"):
        partes.append(
            "El BJJ de esta tarde no recibe estímulo previo; si el dolor o la fatiga "
            "persisten al mediodía, considera reducirlo a técnico o no entrenar. "
            "No uses analgésicos para forzar la sesión (docs/04)."
        )
    if incertidumbres:
        partes.append(" ".join(incertidumbres))
    prop.explicacion = " ".join(partes)
    return prop


def _explicar(prop: Proposal, estado: DailyState, ayer: dict) -> str:
    """Explicación mínima de docs/03: familia y por qué, restricciones,
    carga activa relevante con su origen, e incertidumbre declarada."""
    carga = prop.carga
    partes: list[str] = []

    # Familia elegida y por qué.
    nombre = _NOMBRE_FAMILIA[prop.familia] + (" reducida" if prop.reducida else "")
    if prop.familia == "A":
        motivo = f"Familia A ({nombre}) por BJJ {prop.bjj_efectivo} previsto hoy"
        if estado.bjj_disponible == "incierto":
            motivo = "Familia A: BJJ incierto, se conserva margen como si fuera normal (C5)"
        elif prop.techo != "potente":
            motivo = f"Familia A reducida: techo {prop.techo}"
    elif prop.familia == "B":
        motivo = "Familia B (potente): recuperación verde y sin BJJ hoy (C6 no obliga, pero la avalan)"
    elif prop.familia == "D":
        motivo = "Familia D (técnica): objetivo del día técnico (P2)"
    else:
        motivo = f"Familia C (recuperación): techo {prop.techo}"
    codigos = ", ".join(prop.reglas_aplicadas)
    partes.append(f"{motivo}. Reglas aplicadas: {codigos}.")

    # Carga relevante con origen.
    relevantes = [d for d in DIMENSIONES if carga.niveles[d] in ("media", "alta")]
    if relevantes:
        frag = []
        for d in relevantes:
            origen = "; ".join(carga.origenes.get(d, [])[:3])
            frag.append(f"{d} {carga.puntos[d]:g} ({carga.niveles[d]}) por {origen}")
        partes.append("Carga activa: " + "; ".join(frag) + f". Total {carga.total}.")

    # Restricciones activas.
    if prop.d3_activa:
        partes.append(
            f"BJJ {prop.bjj_efectivo} después: prohibidos ejercicios de impacto lumbar "
            "amarillo o rojo (D3)."
        )
    if prop.d4_activa:
        partes.append("BJJ duro ya cuenta como estímulo lumbar alto del día (D4).")
    if prop.d5_activa:
        partes.append("Ayer hubo bisagra exigente: hoy prohibida la bisagra exigente (D5).")
    if prop.patrones_restringidos:
        frag = [f"{p} ({m})" for p, m in prop.patrones_restringidos.items()]
        partes.append("Patrones restringidos: " + "; ".join(frag) + ".")
    if prop.patrones_dosificados:
        partes.append(
            "Patrones dosificados por carga media (C2): " + ", ".join(prop.patrones_dosificados) + "."
        )
    if prop.patrones_prioritarios:
        partes.append(
            "Patrones frescos prioritarios (P1, > 7 días sin estímulo): "
            + ", ".join(prop.patrones_prioritarios)
            + "."
        )

    # Incertidumbre.
    if prop.incertidumbres:
        partes.append(" ".join(prop.incertidumbres))
    return " ".join(partes)
