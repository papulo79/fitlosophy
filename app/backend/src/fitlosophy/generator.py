"""Generador de sesiones (docs/06).

De familia + presupuesto + patrones prioritarios/restringidos a una sesión
concreta: bloques B0-B4, composición (10 reglas), dosificación por familia,
filtro de material, sustitución y validación final.
Todos los valores numéricos son provisionales (Fase 9).
"""

from __future__ import annotations

from datetime import datetime

from .catalog import PUNTOS_COSTE, Catalog, Exercise
from .engine import PATRONES_FAMILIA
from .load import puntos_registro, ultimo_uso_por_ejercicio
from .models import DailyState, Event, Proposal, SessionItem, SessionProposal

# Orden de bloques y tamaños por plantilla (docs/06).
B1_TAMANO = {"A": (2, 3), "B": (3, 4)}  # (mínimo, máximo); C y D no tienen B1
B2_TAMANO = {"A": (1, 2), "B": (2, 2)}

_RANGO_LUMBAR = {"verde": 0, "amarillo": 1, "rojo": 2}

# Macro-grupos para la cobertura de B1 en familia B (heurística provisional):
# una sesión potente cubre bisagra, empuje y tirón antes que repetir grupo.
_MACRO_GRUPOS = [
    ("bisagra", {"dominante_cadera"}),
    ("empuje", {"empuje_horizontal", "empuje_vertical"}),
    ("tiron", {"tiron_horizontal", "tiron_vertical"}),
    ("pierna", {"dominante_rodilla"}),
    ("core", {"core_antiextension", "core_antirotacion", "core_lateral", "core_flexion_cadera"}),
    ("locomocion", {"acondicionamiento", "agilidad"}),
]

# Pools base de los bloques con selección abierta (regla 10 de docs/06): el
# orden de estas tuplas es el orden de preferencia sin historial; el resto del
# pool se ordena por orden de catálogo detrás.
_B0_BASE = ("dead-bug", "agility-ladder-basic", "glute-bridge")
_B0_PATRONES = {"core_antiextension", "core_antirotacion", "core_lateral", "movilidad_cargada", "agilidad"}
_C_BASE = ("dead-bug", "glute-bridge", "plank-front")
_D_BASE = ("cones-zigzag", "rope-technical", "agility-ladder-basic")


def _clave_variedad(ejercicio: Exercise, ultimo_uso: dict[str, datetime], fecha: datetime):
    """Regla 10: nunca usado primero; luego, más tiempo desde el último uso."""
    uso = ultimo_uso.get(ejercicio.id)
    if uso is None:
        return (0, 0.0)
    return (1, -(fecha - uso).total_seconds())


def _nota_variedad(ejercicio: Exercise, ultimo_uso: dict[str, datetime]) -> str:
    uso = ultimo_uso.get(ejercicio.id)
    if uso is None:
        return " (variedad: nunca usado)"
    return f" (variedad: no usado desde {uso.date().isoformat()})"


def _orden_pool(
    pool: list[Exercise],
    base: tuple[str, ...],
    ultimo_uso: dict[str, datetime],
    fecha: datetime,
) -> list[Exercise]:
    """Ordena un pool (B0, C, D): regla de variedad y, a igualdad, primero la
    lista base en su orden y después el orden de catálogo (sort estable). Sin
    historial el resultado es el orden clásico: lista base y luego catálogo."""
    return sorted(
        pool,
        key=lambda e: (
            _clave_variedad(e, ultimo_uso, fecha),
            base.index(e.id) if e.id in base else len(base),
        ),
    )


def puntos_propuesta(ejercicio: Exercise, familia: str, dosis_minima: bool) -> dict[str, float]:
    """Puntos que un ejercicio computa en la sesión propuesta (docs/06).

    - Base: bajo=1, medio=2, alto=3; patrones secundarios a la mitad (docs/12).
    - Dosis en el extremo bajo del rango (familias A y C): las dimensiones con
      coste `bajo` computan a la mitad; medio/alto computan íntegras.
    - Interpretación documentada (del ejemplo de validación de docs/06, donde el
      press militar en familia B computa core 0.5): una dimensión con coste
      `bajo` que el patrón principal no alimenta (estabilización accesoria)
      computa a la mitad en cualquier familia.
    """
    pts = puntos_registro(ejercicio)
    alimentadas = ejercicio.dimensiones_alimentadas()
    secundarias = ejercicio.dimensiones_secundarias()
    for dim, coste in ejercicio.coste_dimensiones.items():
        if coste != "bajo" or dim in secundarias:
            continue
        if (familia in ("A", "C") and dosis_minima) or dim not in alimentadas:
            pts[dim] = PUNTOS_COSTE[coste] / 2
    return pts


# --- Filtro de candidatos ------------------------------------------------------


def motivos_exclusion(
    ejercicio: Exercise, prop: Proposal, familia: str
) -> list[str]:
    """Razones por las que un ejercicio no puede entrar en la sesión.

    Reúne el filtro de patrones restringidos (regla 6 de composición), las
    reglas duras D3/D4/D5 y las prohibiciones de la plantilla A.
    """
    motivos: list[str] = []
    if ejercicio.patron in prop.patrones_restringidos:
        motivos.append(prop.patrones_restringidos[ejercicio.patron])
    if prop.d3_activa and _RANGO_LUMBAR[ejercicio.impacto_lumbar] >= 1:
        motivos.append(f"D3: impacto lumbar {ejercicio.impacto_lumbar} antes de BJJ {prop.bjj_efectivo}")
    if prop.d4_activa and ejercicio.impacto_lumbar == "rojo":
        motivos.append("D4: BJJ duro ya es el estímulo lumbar alto del día")
    if prop.d5_activa and ejercicio.coste("bisagra") == "alto":
        motivos.append("D5: bisagra exigente prohibida hoy")
    if familia == "A":
        if _RANGO_LUMBAR[ejercicio.impacto_lumbar] >= 1:
            motivos.append("Plantilla A: prohibido impacto lumbar amarillo o rojo")
        if ejercicio.explosivo:
            motivos.append("Plantilla A: prohibidos los ejercicios explosivos")
        if ejercicio.coste("agarre") in ("medio", "alto"):
            motivos.append("Plantilla A: prohibido coste de agarre medio o alto")
    if familia == "C":
        if any(c != "bajo" for c in ejercicio.coste_dimensiones.values()):
            motivos.append("Plantilla C: ningún ejercicio puede superar coste bajo")
        if ejercicio.impacto_lumbar != "verde":
            motivos.append("Plantilla C: impacto lumbar verde obligatorio")
    return motivos


def _candidatos(
    prop: Proposal,
    familia: str,
    catalog: Catalog,
    material: set[str] | frozenset[str],
    patrones: set[str] | None = None,
) -> list[Exercise]:
    permitidos = PATRONES_FAMILIA[familia]
    resultado = []
    for ej in catalog:
        if patrones is not None and ej.patron not in patrones:
            continue
        if ej.patron not in permitidos:
            continue
        if not ej.disponible_con(material):
            continue
        if motivos_exclusion(ej, prop, familia):
            continue
        resultado.append(ej)
    return resultado


# --- Dosificación ----------------------------------------------------------------


def _rango(valor) -> tuple[float, float] | None:
    if isinstance(valor, list) and len(valor) == 2:
        return float(valor[0]), float(valor[1])
    if isinstance(valor, (int, float)):
        return float(valor), float(valor)
    return None


def _dosis(ejercicio: Exercise, familia: str) -> str:
    """Texto de dosis según la tabla de dosificación de docs/06.

    A: extremo bajo del rango. B: rango medio-alto (punto medio redondeado).
    C: mínimo. D: según técnica (extremo bajo-medio).
    """
    p = ejercicio.prescripcion
    dosis_minima = familia in ("A", "C", "D")

    def elige(clave: str) -> float | None:
        r = _rango(p.get(clave))
        if r is None:
            return None
        if familia == "B":
            return round((r[0] + r[1]) / 2)
        return r[0]

    series = elige("series")
    reps = elige("repeticiones")
    segundos = elige("segundos")
    minutos = elige("minutos")
    totales = elige("repeticiones_totales")
    por_lado = " por lado" if p.get("por_lado") else ""

    if minutos is not None:
        # Familia C: movimiento continuo 20-45 min; 30 min es la dosis de los casos de docs/13.
        return f"{int(minutos) if familia != 'C' else 30} min"
    if totales is not None:
        return f"{int(totales)} repeticiones totales"
    if p.get("saltos"):
        s = int(series) if series else int(_rango(p["saltos"])[0])
        return f"{s}×{int(p['saltos'])} saltos"
    if p.get("pasadas_por_patron"):
        r = _rango(p["pasadas_por_patron"])
        # Misma regla de familia que el resto de claves: hoy este ejercicio solo
        # aparece en B0, que ya fuerza dosis mínima (regla 8 de docs/06), pero
        # así no queda una excepción esperando a que se use en otro bloque.
        v = r[0] if dosis_minima else round((r[0] + r[1]) / 2)
        # «por patrón» solo si el catálogo enumera los patrones: si no, la cifra
        # quedaría referida a algo que el usuario no puede ver (docs/05).
        sufijo = " por patrón" if ejercicio.patrones else ""
        return f"{int(v)} pasadas{sufijo}"
    if p.get("recorridos"):
        r = _rango(p["recorridos"])
        v = r[0] if dosis_minima else round((r[0] + r[1]) / 2)
        return f"{int(v)} recorridos"
    if segundos is not None and series is not None:
        return f"{int(series)}×{int(segundos)} s{por_lado}"
    if series is not None and reps is not None:
        return f"{int(series)}×{int(reps)}{por_lado}"
    return "dosis mínima"


def _es_dosis_minima(familia: str) -> bool:
    return familia in ("A", "C")


def dosis_prescrita(ejercicio: Exercise, familia: str) -> str:
    """Dosis legible según la tabla de dosificación de docs/06 (API pública)."""
    return _dosis(ejercicio, familia)


def es_dosis_minima(familia: str) -> bool:
    """True si la familia dosifica en el extremo bajo del rango (A y C)."""
    return _es_dosis_minima(familia)


# --- Construcción de bloques ------------------------------------------------------


def _encaja(puntos: dict[str, float], totales: dict[str, float], presupuestos: dict[str, float]) -> bool:
    for d, p in puntos.items():
        if totales.get(d, 0.0) + p > presupuestos.get(d, 0.0) + 1e-9:
            return False
    return True


def _sumar(puntos: dict[str, float], totales: dict[str, float]) -> None:
    for d, p in puntos.items():
        totales[d] = totales.get(d, 0.0) + p


def _b0(
    catalog: Catalog,
    material,
    ultimo_uso: dict[str, datetime],
    fecha: datetime,
) -> list[SessionItem]:
    """B0 · Calentamiento (no computa en el presupuesto, regla 8).

    Pool (regla 10): coste bajo, `impacto_lumbar` verde y patrones de core,
    movilidad o agilidad; se eligen 2 ordenados por variedad."""
    pool = [
        ej
        for ej in catalog
        if ej.patron in _B0_PATRONES
        and ej.impacto_lumbar == "verde"
        and all(c == "bajo" for c in ej.coste_dimensiones.values())
        and ej.disponible_con(material)
    ]
    base_ids = {e.id for e in _orden_pool(pool, _B0_BASE, {}, fecha)[:2]}
    items: list[SessionItem] = []
    for ej in _orden_pool(pool, _B0_BASE, ultimo_uso, fecha):
        justificacion = "Calentamiento: activación y coordinación (no computa, regla 8)"
        if ultimo_uso and ej.id not in base_ids:
            justificacion += _nota_variedad(ej, ultimo_uso)
        items.append(
            SessionItem(
                exercise_id=ej.id,
                bloque="B0",
                dosis=_dosis(ej, "C"),
                puntos={},
                justificacion=justificacion,
            )
        )
        if len(items) == 2:
            break
    return items


def generate(
    prop: Proposal,
    estado: DailyState,
    catalog: Catalog,
    material_perfil: set[str] | frozenset[str] | None = None,
    historial: list[Event] | None = None,
) -> SessionProposal:
    """Genera la sesión concreta a partir de la salida del motor (docs/06).

    `historial` alimenta la regla de variedad (regla 10); sin él el resultado
    es el orden de preferencia clásico."""
    if estado.material_disponible is None:
        material = set(material_perfil or set())
    else:
        material = set(estado.material_disponible)
    material.add("tatami")  # el tatami cuenta siempre como disponible (el suelo lo sustituye)

    familia = prop.familia
    ultimo_uso = ultimo_uso_por_ejercicio(historial or [])
    notas: list[str] = []
    items: list[SessionItem] = []
    totales: dict[str, float] = {}
    usados_principal: set[str] = set()
    usados_secundario: set[str] = set()
    usados_ids: set[str] = set()

    def anadir(ej: Exercise, bloque: str, justificacion: str) -> bool:
        # Regla 1 de composición: patrón principal único y secundarios no
        # compartidos entre ejercicios de la sesión (B0/B4 no cuentan).
        if ej.id in usados_ids or usados_secundario & set(ej.secundarios):
            return False
        pts = puntos_propuesta(ej, familia, _es_dosis_minima(familia))
        if not _encaja(pts, totales, prop.presupuestos):
            return False
        items.append(
            SessionItem(
                exercise_id=ej.id,
                bloque=bloque,
                dosis=_dosis(ej, familia),
                puntos=pts,
                justificacion=justificacion,
            )
        )
        _sumar(pts, totales)
        usados_principal.add(ej.patron)
        usados_secundario.update(ej.secundarios)
        usados_ids.add(ej.id)
        return True

    items.extend(_b0(catalog, material, ultimo_uso, prop.fecha))
    # B0 no computa ni para la regla 1 de patrones, pero no repetimos ejercicio.
    usados_ids.update(i.exercise_id for i in items)

    if familia == "C":
        _generar_c(prop, catalog, material, anadir, notas, ultimo_uso)
    elif familia == "D":
        _generar_d(prop, catalog, material, anadir, notas, items, ultimo_uso)
    else:
        _generar_ab(prop, catalog, material, familia, anadir, usados_principal, usados_secundario, notas, ultimo_uso)

    _ordenar_bloques(items, catalog)
    sesion = SessionProposal(
        fecha=prop.fecha,
        familia=familia,
        items=items,
        puntos_sesion=totales,
        duracion_estimada_min=_duracion_estimada(items),
        notas=notas,
    )
    _recortar_por_tiempo(sesion, estado, prop)
    validate_session(sesion, prop, catalog)
    return sesion


def _generar_ab(prop, catalog, material, familia, anadir, usados_principal, usados_secundario, notas, ultimo_uso) -> None:
    """Familias A y B: B1 (patrones prioritarios primero, regla 2) + B2 (+ B3 en B)."""
    n_min, n_max = B1_TAMANO[familia]
    # Tamaño objetivo: extremo conservador del rango (interpretación provisional;
    # todos los ejemplos de docs/13 usan el mínimo: A→2, B→3).
    objetivo = n_min

    candidatos = _candidatos(prop, familia, catalog, material)
    por_patron: dict[str, list[Exercise]] = {}
    for ej in candidatos:
        por_patron.setdefault(ej.patron, []).append(ej)

    # Regla 2: patrones prioritarios del motor entran primero en B1.
    orden_patrones: list[str] = []
    if familia == "B":
        # Cobertura por macro-grupos (heurística provisional): bisagra, empuje, tirón, pierna...
        restantes = set(por_patron)
        for _nombre, grupo in _MACRO_GRUPOS:
            disponibles = [p for p in grupo & restantes]
            if disponibles:
                # Dentro del grupo, primero los prioritarios, luego por orden de taxonomía.
                disponibles.sort(key=lambda p: (p not in prop.patrones_prioritarios, catalog.patrones.index(p)))
                orden_patrones.append(disponibles[0])
                restantes.discard(disponibles[0])
        orden_patrones.extend(
            sorted(restantes, key=lambda p: (p not in prop.patrones_prioritarios, catalog.patrones.index(p)))
        )
    else:
        orden_patrones = sorted(
            por_patron, key=lambda p: (p not in prop.patrones_prioritarios, catalog.patrones.index(p))
        )

    anadidos = 0
    for patron in orden_patrones:
        if anadidos >= objetivo:
            break
        if patron in usados_principal:
            continue
        justificacion = f"Patrón {patron}" + (" prioritario (P1)" if patron in prop.patrones_prioritarios else "")
        cands = por_patron[patron]
        base0 = _orden_preferencia(cands, familia)[0].id if ultimo_uso else None
        for candidato in _orden_preferencia(cands, familia, ultimo_uso, prop.fecha):
            just = justificacion
            if base0 is not None and candidato.id != base0:
                just += _nota_variedad(candidato, ultimo_uso)
            if anadir(candidato, "B1", just):
                anadidos += 1
                break

    # Patrones prioritarios sin ejercicio disponible: patrón pendiente (regla 9).
    for patron in prop.patrones_prioritarios:
        if patron not in usados_principal and patron not in por_patron:
            notas.append(
                f"Patrón {patron} pendiente: prioritario pero sin ejercicios disponibles "
                "con el material de hoy (regla 9); se retoma cuando haya material."
            )

    # B2 · Accesorio y core.
    n2_min, n2_max = B2_TAMANO[familia]
    patrones_core = [p for p in ("core_antirotacion", "core_lateral", "core_antiextension") if p not in usados_principal]
    anadidos2 = 0
    for patron in patrones_core:
        if anadidos2 >= n2_min:
            break
        if patron in usados_secundario:
            continue  # regla 1: dos ejercicios no pueden compartir el mismo secundario
        cands = _candidatos(prop, familia, catalog, material, {patron})
        base0 = _orden_preferencia(cands, familia)[0].id if ultimo_uso and cands else None
        for candidato in _orden_preferencia(cands, familia, ultimo_uso, prop.fecha):
            just = f"Accesorio/core ({patron}) dosificado"
            if base0 is not None and candidato.id != base0:
                just += _nota_variedad(candidato, ultimo_uso)
            if anadir(candidato, "B2", just):
                anadidos2 += 1
                break

    # B3 · Acondicionamiento: solo en familia B y si queda presupuesto de cardio.
    if familia == "B":
        cands = _candidatos(prop, familia, catalog, material, {"acondicionamiento"})
        base0 = _orden_preferencia(cands, familia)[0].id if ultimo_uso and cands else None
        for candidato in _orden_preferencia(cands, familia, ultimo_uso, prop.fecha):
            just = "Acondicionamiento específico dentro del presupuesto de cardio"
            if base0 is not None and candidato.id != base0:
                just += _nota_variedad(candidato, ultimo_uso)
            if anadir(candidato, "B3", just):
                break


def _orden_preferencia(
    candidatos: list[Exercise],
    familia: str,
    ultimo_uso: dict[str, datetime] | None = None,
    fecha: datetime | None = None,
) -> list[Exercise]:
    """Orden de preferencia dentro de un patrón.

    - Familias A/C/D: menor nivel primero (más conservador); a igual nivel,
      orden de catálogo.
    - Familia B (día potente): explosivos primero (van primero en B1, docs/06);
      a igualdad, menor impacto lumbar (conservador con este perfil) y mayor
      estímulo total; heurística provisional.
    - Última clave (regla 10): a igualdad de lo anterior, el ejercicio con más
      tiempo sin usarse; nunca usado primero. Sin historial no cambia nada.
    """
    variedad = bool(ultimo_uso) and fecha is not None

    def clave_var(e: Exercise):
        return _clave_variedad(e, ultimo_uso, fecha) if variedad else (0, 0.0)

    if familia == "B":
        return sorted(
            candidatos,
            key=lambda e: (
                not e.explosivo,
                _RANGO_LUMBAR[e.impacto_lumbar],
                -sum(PUNTOS_COSTE[c] for c in e.coste_dimensiones.values()),
                {"base": 0, "intermedio": 1, "avanzado": 2}[e.nivel],
                clave_var(e),
            ),
        )
    return sorted(
        candidatos,
        key=lambda e: ({"base": 0, "intermedio": 1, "avanzado": 2}[e.nivel], clave_var(e)),
    )


def _generar_c(prop, catalog, material, anadir, notas, ultimo_uso) -> None:
    """Familia C: movimiento continuo + B2 ligero, sin B1 (plantilla C).

    Regla 10: el continuo y el B2 ligero salen de pools del catálogo (patrón
    `recuperacion` para el continuo; el resto de candidatos C para B2),
    ordenados por variedad."""
    pool_continuo = [
        ej for ej in _candidatos(prop, "C", catalog, material) if ej.patron == "recuperacion"
    ]
    base_continuo = _orden_pool(pool_continuo, ("treadmill-walk",), {}, prop.fecha)
    for i, ej in enumerate(_orden_pool(pool_continuo, ("treadmill-walk",), ultimo_uso, prop.fecha)):
        just = "Movimiento continuo de baja intensidad (recuperación activa)"
        if ultimo_uso and (i >= len(base_continuo) or ej.id != base_continuo[i].id):
            just += _nota_variedad(ej, ultimo_uso)
        if anadir(ej, "continuo", just):
            break
    else:
        notas.append("Cinta no disponible: movimiento continuo sustituido por movilidad suave.")
    pool_b2 = [
        ej for ej in _candidatos(prop, "C", catalog, material) if ej.patron != "recuperacion"
    ]
    base_b2 = _orden_pool(pool_b2, _C_BASE, {}, prop.fecha)
    anadidos = 0
    for i, ej in enumerate(_orden_pool(pool_b2, _C_BASE, ultimo_uso, prop.fecha)):
        if anadidos >= 2:
            break
        just = "Core/movilidad verde en dosis baja (plantilla C)"
        if ultimo_uso and (i >= len(base_b2) or ej.id != base_b2[i].id):
            just += _nota_variedad(ej, ultimo_uso)
        if anadir(ej, "B2", just):
            anadidos += 1
    notas.append("La sesión debe dejar mejores sensaciones que al comenzar; si no, se recorta (plantilla C).")


def _generar_d(prop, catalog, material, anadir, notas, items, ultimo_uso) -> None:
    """Familia D: B0 + trabajo técnico (escalera, conos, comba técnica).

    Regla 10: pool de agilidad/acondicionamiento del catálogo ordenado por
    variedad. La escalera ya suele estar en B0; no se repite ni patrón ni
    ejercicio (regla 1 de composición)."""
    pool = [ej for ej in _candidatos(prop, "D", catalog, material)]
    base = _orden_pool(pool, _D_BASE, {}, prop.fecha)
    for i, ej in enumerate(_orden_pool(pool, _D_BASE, ultimo_uso, prop.fecha)):
        just = "Trabajo técnico y de agilidad (plantilla D)"
        if ultimo_uso and (i >= len(base) or ej.id != base[i].id):
            just += _nota_variedad(ej, ultimo_uso)
        anadir(ej, "B1", just)


def _ordenar_bloques(items: list[SessionItem], catalog: Catalog) -> None:
    """Orden de bloques y, dentro de B1 (regla 4): explosivos primero, fuerza
    después; los unilaterales van tras los bilaterales."""
    orden_bloque = {"B0": 0, "continuo": 1, "B1": 2, "B2": 3, "B3": 4, "B4": 5}

    def clave(item: SessionItem):
        ej = catalog.get(item.exercise_id)
        explosivo = ej.explosivo if ej else False
        unilateral = ej.lateralidad == "unilateral" if ej else False
        return (orden_bloque.get(item.bloque, 9), not explosivo, unilateral)

    items.sort(key=clave)


def _duracion_estimada(items: list[SessionItem]) -> int:
    """Estimación burda (provisional): B0 8 min; B1 ~3 min/serie; B2 ~2 min/serie;
    B3 ~2 min/serie; bloque continuo según sus minutos."""
    total = 0
    for item in items:
        if item.bloque == "B0":
            total += 8
        elif item.bloque == "continuo":
            try:
                total += int(item.dosis.split()[0])
            except (ValueError, IndexError):
                total += 25
        else:
            series = 3
            if "×" in item.dosis:
                try:
                    series = int(item.dosis.split("×")[0])
                except ValueError:
                    pass
            total += series * (3 if item.bloque == "B1" else 2)
    return total


def _recortar_por_tiempo(sesion: SessionProposal, estado: DailyState, prop: Proposal) -> None:
    """P3 + regla 7: si la duración supera `tiempo_disponible`, recortar en
    orden: B3, B2, series de B1 al mínimo, último ejercicio de B1."""
    if not estado.tiempo_disponible:
        return
    orden = ["B3", "B2", "B1"]
    while sesion.duracion_estimada_min > estado.tiempo_disponible and orden:
        bloque = orden.pop(0)
        candidatos = [i for i in sesion.items if i.bloque == bloque]
        while sesion.duracion_estimada_min > estado.tiempo_disponible and candidatos:
            eliminado = candidatos.pop()
            sesion.items.remove(eliminado)
            sesion.notas.append(
                f"Recorte por tiempo disponible (P3, regla 7): se elimina {eliminado.exercise_id} de {bloque}."
            )
            for d, p in eliminado.puntos.items():
                sesion.puntos_sesion[d] = sesion.puntos_sesion.get(d, 0.0) - p
            sesion.duracion_estimada_min = _duracion_estimada(sesion.items)
    if sesion.duracion_estimada_min > estado.tiempo_disponible:
        sesion.notas.append(
            "Tiempo insuficiente para el mínimo de la familia (P3): considera familia C."
        )


# --- Validación final -------------------------------------------------------------


def validate_session(
    sesion: SessionProposal, prop: Proposal, catalog: Catalog
) -> SessionProposal:
    """Validación final de docs/06. Marca `valida`, `violaciones` y recomputa
    `puntos_sesion` a partir de los items."""
    totales: dict[str, float] = {}
    for item in sesion.items:
        if item.bloque in ("B0", "B4"):
            continue  # regla 8: no computan
        for d, p in item.puntos.items():
            totales[d] = totales.get(d, 0.0) + p
    sesion.puntos_sesion = totales

    violaciones: list[str] = []
    for d, p in totales.items():
        if p > prop.presupuestos.get(d, 0.0) + 1e-9:
            violaciones.append(
                f"Dimensión {d}: {p:g} puntos supera el presupuesto {prop.presupuestos.get(d, 0.0):g}"
            )

    computables = [i for i in sesion.items if i.bloque not in ("B0", "B4")]
    principales: set[str] = set()
    secundarios_usados: set[str] = set()
    for item in computables:
        ej = catalog.get(item.exercise_id)
        if ej is None:
            continue
        if ej.patron in principales:
            violaciones.append(f"Patrón principal repetido: {ej.patron} (regla 1)")
        principales.add(ej.patron)
        for sec in ej.secundarios:
            if sec in secundarios_usados:
                violaciones.append(f"Patrón secundario compartido: {sec} (regla 1)")
            secundarios_usados.add(sec)

    # Reglas duras sobre la selección final.
    for item in computables:
        ej = catalog.get(item.exercise_id)
        if ej is None:
            continue
        motivos = motivos_exclusion(ej, prop, sesion.familia)
        violaciones.extend(f"{ej.id}: {m}" for m in motivos)

    # D4 / regla 3: máximo un estímulo lumbar alto; sin amarillo si hay rojo o BJJ duro.
    rojos = [i for i in computables if catalog.get(i.exercise_id) and catalog[i.exercise_id].impacto_lumbar == "rojo"]
    amarillos = [i for i in computables if catalog.get(i.exercise_id) and catalog[i.exercise_id].impacto_lumbar == "amarillo"]
    if len(rojos) > 1:
        violaciones.append("Más de un ejercicio de impacto lumbar rojo (D4, regla 3)")
    if rojos and (amarillos or prop.d4_activa):
        violaciones.append("Impacto lumbar rojo combinado con amarillo o BJJ duro (D4, regla 3)")
    if rojos and sesion.familia != "B":
        violaciones.append("Impacto lumbar rojo fuera de familia B (regla 3)")

    sesion.violaciones = violaciones
    sesion.valida = not violaciones
    return sesion


# --- Sustitución ---------------------------------------------------------------------


def check_substitution(
    original: Exercise,
    candidato: Exercise,
    prop: Proposal,
    familia: str,
    catalog: Catalog,
    puntos_actuales: dict[str, float] | None = None,
) -> tuple[bool, list[str]]:
    """Reglas de sustitución de docs/06. Devuelve (válida, motivos de rechazo)."""
    motivos: list[str] = []
    dosis_minima = _es_dosis_minima(familia)

    # 1. Mismo patrón principal y mismo objetivo en el bloque.
    if candidato.patron != original.patron:
        motivos.append(f"Patrón distinto: {candidato.patron} no es {original.patron} (regla 1)")

    # 2. Impacto lumbar no superior.
    if _RANGO_LUMBAR[candidato.impacto_lumbar] > _RANGO_LUMBAR[original.impacto_lumbar]:
        motivos.append(
            f"Impacto lumbar {candidato.impacto_lumbar} superior al original {original.impacto_lumbar} (regla 2)"
        )

    # 3. No empeora ninguna dimensión con presupuesto en 0 o 1 punto (umbral crítico provisional).
    pts_orig = puntos_propuesta(original, familia, dosis_minima)
    pts_cand = puntos_propuesta(candidato, familia, dosis_minima)
    for d in set(pts_cand) | set(pts_orig):
        incremento = pts_cand.get(d, 0.0) - pts_orig.get(d, 0.0)
        if incremento <= 0:
            continue
        restante = prop.presupuestos.get(d, 0.0)
        if puntos_actuales is not None:
            restante = max(prop.presupuestos.get(d, 0.0) - puntos_actuales.get(d, 0.0) + pts_orig.get(d, 0.0), 0.0)
        if restante <= 1.0 or incremento > restante + 1e-9:
            motivos.append(
                f"Empeora {d} (+{incremento:g}) con presupuesto crítico ({restante:g} puntos) (regla 3)"
            )

    # 4. No restringido por el motor ni violación de D3-D5.
    motivos.extend(motivos_exclusion(candidato, prop, familia))

    return (not motivos, motivos)


def find_substitute(
    original: Exercise,
    prop: Proposal,
    familia: str,
    catalog: Catalog,
    puntos_actuales: dict[str, float] | None = None,
) -> Exercise | None:
    """Orden de búsqueda de docs/06: sustitutos del catálogo → familia de
    progresión/regresión → cualquier ejercicio del patrón que cumpla 1-4."""
    vistos: set[str] = {original.id}

    def intenta(ids) -> Exercise | None:
        for eid in ids:
            if eid in vistos:
                continue
            vistos.add(eid)
            ej = catalog.get(eid)
            if ej is None:
                continue
            ok, _ = check_substitution(original, ej, prop, familia, catalog, puntos_actuales)
            if ok:
                return ej
        return None

    return (
        intenta(original.sustitutos)
        or intenta((*original.regresiones, *original.progresiones))
        or intenta(e.id for e in catalog if e.patron == original.patron)
    )
