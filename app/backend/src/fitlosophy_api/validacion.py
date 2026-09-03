"""Validación determinista de una entrada candidata para `data/ejercicios.yaml`.

Comprueba todo lo comprobable —dominios cerrados, inventario de material,
referencias cruzadas, unicidad, coherencia de la prescripción— para que el
criterio humano se reserve a lo que lo necesita (cobertura, impacto lumbar
correcto para el atleta, costes plausibles).

La usa `scripts/validar_ejercicio.py` desde la línea de órdenes y el endpoint
de aceptación de candidatos (`routes.py`): misma puerta, dos entradas.
"""

from __future__ import annotations

from fitlosophy.catalog import INTENCION_POR_OBJETIVO, MATERIAL_A_PERFIL

OBLIGATORIOS = (
    "id",
    "nombre",
    "descripcion",
    "patron",
    "nivel",
    "lateralidad",
    "coste_dimensiones",
    "impacto_lumbar",
    "compatibilidad_bjj",
    "objetivos",
    "prescripcion",
)

# Claves admitidas en `prescripcion` (las que sabe interpretar el generador).
CLAVES_PRESCRIPCION = {
    "series",
    "repeticiones",
    "repeticiones_totales",
    "segundos",
    "minutos",
    "saltos",
    "pasadas_por_patron",
    "recorridos",
    "reserva_repeticiones",
    "por_lado",
    "evitar_fallo",
    "detener_si_falla_tecnica",
    "sin_balanceo",
}
CLAVES_RANGO = {
    "series",
    "repeticiones",
    "repeticiones_totales",
    "segundos",
    "minutos",
    "pasadas_por_patron",
    "recorridos",
    "reserva_repeticiones",
}

# Señales de que la descripción declara el límite con palabras (docs/05).
SEÑALES_RIESGO = ("lumbar", "espalda", "rotación", "molestia", "despacio")


class Informe:
    def __init__(self) -> None:
        self.errores: list[str] = []
        self.avisos: list[str] = []

    def error(self, msg: str) -> None:
        self.errores.append(msg)

    def aviso(self, msg: str) -> None:
        self.avisos.append(msg)


def _dominios(catalogo) -> dict:
    return catalogo.valores or {}


def validar(propuesta: dict, catalogo, perfil, permitir_verde: bool) -> Informe:
    inf = Informe()
    val = _dominios(catalogo)
    ids_existentes = {e.id for e in catalogo}

    for campo in OBLIGATORIOS:
        if not propuesta.get(campo):
            inf.error(f"Falta el campo obligatorio «{campo}»")
    if inf.errores:
        return inf  # sin los básicos, el resto de comprobaciones no informa

    eid = propuesta["id"]
    if eid in ids_existentes:
        inf.error(f"El id «{eid}» ya existe en el catálogo")
    if eid != eid.lower() or " " in eid or "_" in eid:
        inf.error(f"El id «{eid}» debe ir en kebab-case y minúsculas (ej. kb-swing-two-hand)")
    if not eid.isascii():
        inf.error(f"El id «{eid}» debe ir en inglés y sin acentos")

    # --- dominios cerrados ---
    for campo, clave in (
        ("patron", "patron"),
        ("nivel", "nivel"),
        ("lateralidad", "lateralidad"),
        ("impacto_lumbar", "impacto_lumbar"),
        ("compatibilidad_bjj", "compatibilidad_bjj"),
    ):
        permitidos = val.get(clave, [])
        if permitidos and propuesta[campo] not in permitidos:
            inf.error(
                f"«{campo}: {propuesta[campo]}» no está en el dominio: {', '.join(permitidos)}"
            )

    for sec in propuesta.get("secundarios", []) or []:
        if sec not in val.get("patron", []):
            inf.error(f"Patrón secundario desconocido: «{sec}»")

    # --- material ---
    for m in propuesta.get("material", []) or []:
        if m not in MATERIAL_A_PERFIL:
            inf.error(
                f"Material desconocido: «{m}». Disponibles: {', '.join(sorted(MATERIAL_A_PERFIL))}"
            )
        elif m != "tatami" and m not in perfil.material:
            inf.aviso(f"«{m}» no está en el inventario del perfil: el ejercicio nunca se propondrá")

    # --- coste por dimensión ---
    costes = propuesta["coste_dimensiones"]
    if not isinstance(costes, dict) or not costes:
        inf.error("«coste_dimensiones» debe ser un mapa dimensión → nivel y no puede estar vacío")
    else:
        for dim, nivel in costes.items():
            if dim not in val.get("dimensiones", []):
                inf.error(f"Dimensión desconocida en coste_dimensiones: «{dim}»")
            if nivel not in val.get("nivel_coste", []):
                inf.error(f"Nivel de coste inválido para «{dim}»: «{nivel}»")

    # --- referencias cruzadas ---
    for campo in ("sustitutos", "progresiones", "regresiones"):
        for ref in propuesta.get(campo, []) or []:
            if ref not in ids_existentes:
                inf.error(f"«{campo}» apunta a un id que no existe: «{ref}»")

    # --- descripción (docs/05) ---
    desc = (propuesta["descripcion"] or "").strip()
    if desc.lower().startswith(propuesta["nombre"].lower()):
        inf.error("La descripción no debe empezar repitiendo el nombre del ejercicio")
    if "×" in desc:
        inf.error("La descripción no debe llevar la dosis: sale de «prescripcion»")
    if propuesta["impacto_lumbar"] == "rojo" and not any(s in desc.lower() for s in SEÑALES_RIESGO):
        inf.error(
            "Un ejercicio de impacto lumbar rojo debe declarar su límite con palabras "
            "en la descripción, no solo con la etiqueta"
        )

    # --- prescripción ---
    presc = propuesta["prescripcion"]
    if not isinstance(presc, dict) or not presc:
        inf.error("«prescripcion» debe ser un mapa y no puede estar vacío")
    else:
        for clave, valor in presc.items():
            if clave not in CLAVES_PRESCRIPCION:
                inf.error(f"Clave de prescripción desconocida: «{clave}»")
            elif clave in CLAVES_RANGO and isinstance(valor, list):
                if len(valor) != 2 or valor[0] > valor[1]:
                    inf.error(f"«{clave}: {valor}» debe ser un rango creciente de dos elementos")
        if presc.get("pasadas_por_patron") and not propuesta.get("patrones"):
            inf.error("Dosifica por patrón: «patrones» debe enumerarlos (docs/05)")
    if propuesta.get("patrones") and not (presc or {}).get("pasadas_por_patron"):
        inf.error("«patrones» sin «pasadas_por_patron»: la lista no tendría cifra que aplicarle")

    # --- intención derivada ---
    primero = (propuesta["objetivos"] or [""])[0]
    if primero not in INTENCION_POR_OBJETIVO:
        inf.aviso(
            f"El objetivo principal «{primero}» no está mapeado a ninguna intención: "
            "se mostrará «control» por defecto (ver docs/05)"
        )

    # --- puerta de seguridad lumbar ---
    if propuesta["impacto_lumbar"] == "verde" and not permitir_verde:
        inf.error(
            "Un ejercicio nuevo no entra como «impacto_lumbar: verde» sin confirmación "
            "explícita: relanza con --confirmo-verde si lo has revisado tú "
            "(AGENTS.md: no relajar restricciones lumbares sin instrucción explícita)"
        )

    return inf


def cobertura(propuesta: dict, catalogo) -> list[str]:
    """Qué cubre ya el catálogo en ese patrón: convierte «¿aporta algo?» en una
    comparación en vez de una pregunta abierta."""
    patron = propuesta.get("patron")
    hermanos = [e for e in catalogo if e.patron == patron]
    lineas = [f"Ya hay {len(hermanos)} ejercicio(s) con patrón «{patron}»:"]
    for e in hermanos:
        material = ", ".join(e.material) or "sin material"
        lineas.append(f"  · {e.nombre} ({material}) — lumbar {e.impacto_lumbar}, nivel {e.nivel}")
    if not hermanos:
        lineas.append("  · ninguno: cubre un patrón que hoy está vacío")
    return lineas
