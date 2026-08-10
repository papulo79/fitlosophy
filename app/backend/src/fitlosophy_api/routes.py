"""Rutas de la API del MVP (docs/14).

Toda la lógica de decisión está en el paquete `fitlosophy`; estas rutas solo
orquestan: persisten el estado diario, llaman al motor y al generador, guardan
la propuesta, gestionan la ejecución y el cierre, y exponen el historial.
"""

from __future__ import annotations

import sqlite3
import threading
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from fitlosophy.catalog import MATERIAL_A_PERFIL, Catalog, perfil_desde_dict
from fitlosophy.engine import decide
from fitlosophy.generator import (
    check_substitution,
    dosis_prescrita,
    es_dosis_minima,
    generate,
    puntos_propuesta,
    validate_session,
)
from fitlosophy.models import DailyState, Proposal, SessionItem, SessionProposal

from .auth import LoginIn, login, logout, usuario_actual
from .db import cargar_json, volcar_json
from .history import construir_historial, dimensiones_de_molestias
from .schemas import (
    BjjIn,
    BjjPut,
    CierreIn,
    CierrePut,
    EstadoDiarioIn,
    FinalizarIn,
    ItemPatchIn,
    PerfilPut,
    SesionIn,
    SesionPut,
    SustituirIn,
)

router = APIRouter()

# RPE previsto por familia (plantillas de docs/06).
RPE_PREVISTO = {"A": "5-6", "B": "7-8", "C": "2-4", "D": "modulable según BJJ"}

TOKENS_MATERIAL = set(MATERIAL_A_PERFIL)


# --- Dependencias y helpers ------------------------------------------------------


def db_conn(request: Request):
    """Conexión única serializada (app personal de un solo usuario)."""
    with request.app.state.lock:
        yield request.app.state.db


def get_catalog(request: Request) -> Catalog:
    return request.app.state.catalog


def get_perfil(conn: sqlite3.Connection):
    fila = conn.execute("SELECT data FROM profile WHERE id = 1").fetchone()
    if fila is None:
        from fitlosophy.catalog import load_default_perfil

        return load_default_perfil()
    return perfil_desde_dict(cargar_json(fila["data"], {}))


def _prop_desde_fila(row: sqlite3.Row) -> Proposal:
    return Proposal(
        fecha=datetime.fromisoformat(row["fecha"]),
        familia=row["familia"],
        reducida=bool(row["reducida"]),
        techo=row["techo"] or "potente",
        bjj_efectivo=row["bjj_efectivo"],
        presupuestos=cargar_json(row["presupuestos"], {}),
        patrones_prioritarios=cargar_json(row["patrones_prioritarios"], []),
        patrones_restringidos=cargar_json(row["patrones_restringidos"], {}),
        patrones_dosificados=cargar_json(row["patrones_dosificados"], []),
        d3_activa=bool(row["d3"]),
        d4_activa=bool(row["d4"]),
        d5_activa=bool(row["d5"]),
        reglas_aplicadas=cargar_json(row["reglas"], []),
        incertidumbres=cargar_json(row["incertidumbres"], []),
        explicacion=row["explicacion"],
    )


def _totales_items(items: list[dict]) -> dict[str, float]:
    totales: dict[str, float] = {}
    for it in items:
        if it["bloque"] in ("B0", "B4"):
            continue
        for d, p in (it.get("puntos") or {}).items():
            totales[d] = totales.get(d, 0.0) + p
    return totales


def _propuesta_json(row: sqlite3.Row, catalog: Catalog) -> dict:
    items = cargar_json(row["items"], [])
    for it in items:
        ej = catalog.get(it["exercise_id"])
        it["nombre"] = ej.nombre if ej else it["exercise_id"]
        # Ejecución para el usuario (docs/05): no se persiste con la propuesta,
        # se resuelve desde el catálogo para que un cambio en él se refleje al
        # instante en las sesiones ya guardadas.
        it["descripcion"] = ej.descripcion if ej else ""
        it["patrones"] = list(ej.patrones) if ej else []
    return {
        "id": row["id"],
        "estado_diario_id": row["daily_state_id"],
        "estado": row["estado"],
        "fecha": row["fecha"],
        "familia": row["familia"],
        "reducida": bool(row["reducida"]),
        "techo": row["techo"],
        "bjj_efectivo": row["bjj_efectivo"],
        "rpe_previsto": row["rpe_previsto"],
        "explicacion": row["explicacion"],
        "reglas_aplicadas": cargar_json(row["reglas"], []),
        "incertidumbres": cargar_json(row["incertidumbres"], []),
        "presupuestos": cargar_json(row["presupuestos"], {}),
        "patrones_prioritarios": cargar_json(row["patrones_prioritarios"], []),
        "patrones_restringidos": cargar_json(row["patrones_restringidos"], {}),
        "patrones_dosificados": cargar_json(row["patrones_dosificados"], []),
        "d3_activa": bool(row["d3"]),
        "d4_activa": bool(row["d4"]),
        "d5_activa": bool(row["d5"]),
        "carga": cargar_json(row["carga"], {}),
        "items": items,
        "puntos_sesion": _totales_items(items),
        "notas": cargar_json(row["notas"], []),
        "duracion_estimada_min": row["duracion_estimada_min"],
        "valida": bool(row["valida"]),
        "violaciones": cargar_json(row["violaciones"], []),
    }


def _guardar_propuesta(conn, estado_id: int, prop: Proposal, sesion: SessionProposal) -> int:
    # Volver a declarar el estado diario sustituye la propuesta anterior del día
    # en lugar de acumularla (docs/14): el estado real cambia a lo largo de la
    # tarde, pero solo una propuesta está vigente en cada momento.
    conn.execute(
        "UPDATE proposals SET estado = 'descartada' WHERE estado = 'vigente' AND date(fecha) = date(?)",
        (prop.fecha.isoformat(timespec="seconds"),),
    )
    items = [
        {
            "exercise_id": i.exercise_id,
            "bloque": i.bloque,
            "dosis": i.dosis,
            "puntos": i.puntos,
            "justificacion": i.justificacion,
        }
        for i in sesion.items
    ]
    carga = prop.carga
    cur = conn.execute(
        """INSERT INTO proposals (
            daily_state_id, fecha, familia, reducida, techo, bjj_efectivo, rpe_previsto,
            presupuestos, patrones_prioritarios, patrones_restringidos, patrones_dosificados,
            d3, d4, d5, reglas, incertidumbres, explicacion, carga, items, notas,
            duracion_estimada_min, valida, violaciones, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            estado_id,
            prop.fecha.isoformat(timespec="seconds"),
            prop.familia,
            int(prop.reducida),
            prop.techo,
            prop.bjj_efectivo,
            RPE_PREVISTO.get(prop.familia, ""),
            volcar_json(prop.presupuestos),
            volcar_json(prop.patrones_prioritarios),
            volcar_json(prop.patrones_restringidos),
            volcar_json(prop.patrones_dosificados),
            int(prop.d3_activa),
            int(prop.d4_activa),
            int(prop.d5_activa),
            volcar_json(prop.reglas_aplicadas),
            volcar_json(prop.incertidumbres),
            prop.explicacion,
            volcar_json(
                {
                    "puntos": carga.puntos if carga else {},
                    "niveles": carga.niveles if carga else {},
                    "total": carga.total if carga else "baja",
                    "restringidas": carga.restringidas if carga else [],
                    "origenes": carga.origenes if carga else {},
                }
            ),
            volcar_json(items),
            volcar_json(sesion.notas),
            sesion.duracion_estimada_min,
            int(sesion.valida),
            volcar_json(sesion.violaciones),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    return int(cur.lastrowid)


# --- Auth (docs/14: acceso) --------------------------------------------------------


@router.post("/api/auth/login")
def ruta_login(datos: LoginIn, request: Request, response: Response, conn=Depends(db_conn)):
    return login(conn, datos, request, response)


@router.post("/api/auth/logout")
def ruta_logout(request: Request, response: Response, conn=Depends(db_conn)):
    return logout(conn, request, response)


@router.get("/api/auth/me")
def ruta_me(user=Depends(usuario_actual)):
    return {"username": user["username"]}


# --- 1. Estado diario → propuesta (criterio 2) --------------------------------------


def _sesion_activa(conn) -> sqlite3.Row | None:
    """Sesión `en_curso`, si la hay. El flujo del MVP admite una como mucho
    (docs/14): mientras exista, no se empieza otra."""
    return conn.execute(
        "SELECT * FROM training_sessions WHERE estado = 'en_curso' ORDER BY id DESC LIMIT 1"
    ).fetchone()


def _exigir_sin_sesion_activa(conn) -> None:
    activa = _sesion_activa(conn)
    if activa is not None:
        raise HTTPException(
            status_code=409,
            detail={
                "detalle": "Ya tienes una sesión en curso. Termínala o cancélala antes de empezar otra.",
                "sesion_id": activa["id"],
            },
        )


@router.post("/api/estado-diario", status_code=201)
def crear_estado_diario(datos: EstadoDiarioIn, request: Request, user=Depends(usuario_actual), conn=Depends(db_conn)):
    catalog = get_catalog(request)
    _exigir_sin_sesion_activa(conn)
    if datos.material_disponible is not None:
        desconocidos = sorted(set(datos.material_disponible) - TOKENS_MATERIAL)
        if desconocidos:
            raise HTTPException(status_code=422, detail=f"Material desconocido: {', '.join(desconocidos)}")

    perfil = get_perfil(conn)
    ahora = datetime.now()
    estado = DailyState(
        fecha=ahora,
        recuperacion=datos.recuperacion,
        dolor=datos.dolor,
        bjj_disponible=datos.bjj_disponible,
        zona_dolor=datos.zona_dolor,
        tipo_bjj=datos.tipo_bjj,
        limitacion=datos.limitacion,
        material_disponible=None if datos.material_disponible is None else frozenset(datos.material_disponible),
        tiempo_disponible=datos.tiempo_disponible,
        preferencia=datos.preferencia,
        circunstancias=datos.circunstancias,
    )
    historial = construir_historial(conn, catalog)
    prop = decide(estado, historial, catalog)
    sesion = generate(prop, estado, catalog, perfil.material)

    cur = conn.execute(
        """INSERT INTO daily_states (
            fecha, recuperacion, dolor, zona_dolor, bjj_disponible, tipo_bjj, limitacion,
            sueno, tiempo_disponible, preferencia, circunstancias, material_disponible, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            ahora.isoformat(timespec="seconds"),
            datos.recuperacion,
            datos.dolor,
            datos.zona_dolor,
            datos.bjj_disponible,
            datos.tipo_bjj,
            datos.limitacion,
            datos.sueno,
            datos.tiempo_disponible,
            datos.preferencia,
            datos.circunstancias,
            None if datos.material_disponible is None else volcar_json(sorted(datos.material_disponible)),
            ahora.isoformat(timespec="seconds"),
        ),
    )
    estado_id = int(cur.lastrowid)
    propuesta_id = _guardar_propuesta(conn, estado_id, prop, sesion)
    conn.commit()

    row = conn.execute("SELECT * FROM proposals WHERE id = ?", (propuesta_id,)).fetchone()
    return {"estado_diario_id": estado_id, "propuesta": _propuesta_json(row, catalog)}


# --- 2. Sustitución de un ítem de la propuesta (criterio 8) ---------------------------


@router.post("/api/propuestas/{propuesta_id}/sustituir")
def sustituir_item(propuesta_id: int, datos: SustituirIn, request: Request, user=Depends(usuario_actual), conn=Depends(db_conn)):
    catalog = get_catalog(request)
    row = conn.execute("SELECT * FROM proposals WHERE id = ?", (propuesta_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")
    aceptada = conn.execute(
        "SELECT COUNT(*) FROM training_sessions WHERE proposal_id = ?", (propuesta_id,)
    ).fetchone()[0]
    if aceptada:
        raise HTTPException(status_code=409, detail="La propuesta ya fue aceptada; la sustitución se registra en la sesión")

    items = cargar_json(row["items"], [])
    if datos.item_indice >= len(items):
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    original = catalog.get(items[datos.item_indice]["exercise_id"])
    candidato = catalog.get(datos.exercise_id)
    if original is None or candidato is None:
        raise HTTPException(status_code=422, detail="Ejercicio desconocido en el catálogo")

    prop = _prop_desde_fila(row)
    ok, motivos = check_substitution(
        original, candidato, prop, row["familia"], catalog, puntos_actuales=_totales_items(items)
    )
    if not ok:
        # Criterio 8: las sustituciones que violan reglas se rechazan con su motivo.
        raise HTTPException(status_code=409, detail={"detalle": "Sustitución rechazada", "motivos": motivos})

    items[datos.item_indice] = {
        "exercise_id": candidato.id,
        "bloque": items[datos.item_indice]["bloque"],
        "dosis": dosis_prescrita(candidato, row["familia"]),
        "puntos": puntos_propuesta(candidato, row["familia"], es_dosis_minima(row["familia"])),
        "justificacion": items[datos.item_indice].get("justificacion", "") + " (sustituido por el usuario)",
    }
    sesion = SessionProposal(
        fecha=prop.fecha,
        familia=row["familia"],
        items=[
            SessionItem(
                exercise_id=it["exercise_id"], bloque=it["bloque"], dosis=it["dosis"],
                puntos=it.get("puntos") or {}, justificacion=it.get("justificacion", ""),
            )
            for it in items
        ],
    )
    validate_session(sesion, prop, catalog)
    conn.execute(
        "UPDATE proposals SET items = ?, valida = ?, violaciones = ? WHERE id = ?",
        (volcar_json(items), int(sesion.valida), volcar_json(sesion.violaciones), propuesta_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM proposals WHERE id = ?", (propuesta_id,)).fetchone()
    return {"propuesta": _propuesta_json(row, catalog)}


# --- 3. Ejecución y registro -----------------------------------------------------------


def _sesion_json(conn, row, catalog) -> dict:
    items = []
    for it in conn.execute("SELECT * FROM session_items WHERE session_id = ? ORDER BY id", (row["id"],)).fetchall():
        ej = catalog.get(it["exercise_id_real"] or it["exercise_id"])
        items.append(
            {
                "id": it["id"],
                "bloque": it["bloque"],
                "exercise_id": it["exercise_id"],
                "exercise_id_real": it["exercise_id_real"],
                "nombre": ej.nombre if ej else (it["exercise_id_real"] or it["exercise_id"]),
                "descripcion": ej.descripcion if ej else "",
                "patrones": list(ej.patrones) if ej else [],
                "dosis": it["dosis"],
                "puntos_previstos": cargar_json(it["puntos_previstos"], {}),
                "justificacion": it["justificacion"],
                "estado": it["estado"],
                "real": {
                    "series": it["series_real"],
                    "repeticiones": it["repeticiones_real"],
                    "segundos": it["segundos_real"],
                    "minutos": it["minutos_real"],
                    "carga_kg": it["carga_kg_real"],
                },
                "motivo": it["motivo"],
                "puntos_reales": cargar_json(it["puntos_reales"], None),
            }
        )
    cierre = conn.execute("SELECT * FROM session_closures WHERE session_id = ?", (row["id"],)).fetchone()
    return {
        "id": row["id"],
        "proposal_id": row["proposal_id"],
        "fecha": row["fecha"],
        "familia": row["familia"],
        "estado": row["estado"],
        "rpe_real": row["rpe_real"],
        "items": items,
        "cierre": None
        if cierre is None
        else {
            "sensacion": cierre["sensacion"],
            "molestias": cargar_json(cierre["molestias"], []),
            "dimensiones_congeladas": cargar_json(cierre["dimensiones_congeladas"], []),
        },
    }


@router.post("/api/sesiones", status_code=201)
def aceptar_propuesta(datos: SesionIn, request: Request, user=Depends(usuario_actual), conn=Depends(db_conn)):
    catalog = get_catalog(request)
    prop = conn.execute("SELECT * FROM proposals WHERE id = ?", (datos.proposal_id,)).fetchone()
    if prop is None:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")
    existente = conn.execute(
        "SELECT id FROM training_sessions WHERE proposal_id = ?", (datos.proposal_id,)
    ).fetchone()
    if existente is not None:
        raise HTTPException(status_code=409, detail="La propuesta ya tiene una sesión en curso o registrada")
    # Una sola sesión activa a la vez (docs/14). Sin esto, recargar la página
    # llevaba al estado diario y aceptar de nuevo abría una segunda sesión.
    _exigir_sin_sesion_activa(conn)
    if prop["estado"] == "descartada":
        raise HTTPException(
            status_code=409,
            detail="Esa propuesta quedó descartada al declarar de nuevo el estado diario",
        )

    ahora = datetime.now()
    cur = conn.execute(
        "INSERT INTO training_sessions (proposal_id, fecha, familia, estado, created_at) VALUES (?, ?, ?, 'en_curso', ?)",
        (datos.proposal_id, ahora.isoformat(timespec="seconds"), prop["familia"], ahora.isoformat(timespec="seconds")),
    )
    sesion_id = int(cur.lastrowid)
    for it in cargar_json(prop["items"], []):
        conn.execute(
            """INSERT INTO session_items (session_id, bloque, exercise_id, dosis, puntos_previstos, justificacion)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sesion_id, it["bloque"], it["exercise_id"], it["dosis"], volcar_json(it.get("puntos") or {}), it.get("justificacion", "")),
        )
    conn.execute("UPDATE proposals SET estado = 'aceptada' WHERE id = ?", (datos.proposal_id,))
    conn.commit()
    row = conn.execute("SELECT * FROM training_sessions WHERE id = ?", (sesion_id,)).fetchone()
    return {"sesion": _sesion_json(conn, row, catalog)}


@router.post("/api/sesiones/{sesion_id}/cancelar")
def cancelar_sesion(sesion_id: int, request: Request, user=Depends(usuario_actual), conn=Depends(db_conn)):
    """Descarta una sesión para que no cuente en el historial (docs/14).

    Vale desde `en_curso` (empezada por error o plan que se cae) y desde
    `finalizada` (se dio por hecha por error): esta última **ya estaba
    aportando carga**, porque `construir_historial` lee las finalizadas, así
    que cancelarla es una corrección de registro (criterio 7 de docs/14).

    Desde `cerrada` no: ahí el cierre pudo congelar la ventana de una dimensión
    y la corrección se hace por ítem desde el historial.
    """
    catalog = get_catalog(request)
    sesion = conn.execute("SELECT * FROM training_sessions WHERE id = ?", (sesion_id,)).fetchone()
    if sesion is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if sesion["estado"] not in ("en_curso", "finalizada"):
        raise HTTPException(
            status_code=409,
            detail=(
                "Solo se cancela una sesión en curso o finalizada sin cerrar; "
                "una sesión cerrada se corrige por ítem desde el historial"
            ),
        )
    conn.execute("UPDATE training_sessions SET estado = 'cancelada' WHERE id = ?", (sesion_id,))
    conn.commit()
    row = conn.execute("SELECT * FROM training_sessions WHERE id = ?", (sesion_id,)).fetchone()
    return {"sesion": _sesion_json(conn, row, catalog)}


@router.get("/api/hoy")
def estado_de_hoy(request: Request, user=Depends(usuario_actual), conn=Depends(db_conn)):
    """Qué hay en marcha ahora mismo, para recuperar el flujo al abrir la app.

    El estado del frontend vive en memoria y se pierde al recargar; sin este
    endpoint, reabrir a mitad de sesión llevaba al estado diario y acababa
    creando una propuesta y una sesión nuevas.
    """
    catalog = get_catalog(request)
    activa = _sesion_activa(conn)
    # Finalizada pero sin cierre: falta la respuesta posterior, que es la que
    # congela la ventana de una dimensión tras una molestia (docs/12,
    # criterio 5). Si no se devolviera, recargar en esa pantalla la perdería
    # en silencio y sin manera de volver.
    pendiente_cierre = conn.execute(
        "SELECT * FROM training_sessions WHERE estado = 'finalizada' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    hoy = datetime.now().date().isoformat()
    propuesta = conn.execute(
        "SELECT * FROM proposals WHERE estado = 'vigente' AND date(fecha) = date(?) "
        "ORDER BY id DESC LIMIT 1",
        (hoy,),
    ).fetchone()
    return {
        "sesion_activa": _sesion_json(conn, activa, catalog) if activa is not None else None,
        "sesion_pendiente_cierre": (
            _sesion_json(conn, pendiente_cierre, catalog) if pendiente_cierre is not None else None
        ),
        "propuesta_vigente": _propuesta_json(propuesta, catalog) if propuesta is not None else None,
    }


@router.get("/api/sesiones/{sesion_id}")
def obtener_sesion(sesion_id: int, request: Request, user=Depends(usuario_actual), conn=Depends(db_conn)):
    row = conn.execute("SELECT * FROM training_sessions WHERE id = ?", (sesion_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    return {"sesion": _sesion_json(conn, row, get_catalog(request))}


@router.patch("/api/sesiones/{sesion_id}/items/{item_id}")
def marcar_item(sesion_id: int, item_id: int, datos: ItemPatchIn, request: Request, user=Depends(usuario_actual), conn=Depends(db_conn)):
    catalog = get_catalog(request)
    sesion = conn.execute("SELECT * FROM training_sessions WHERE id = ?", (sesion_id,)).fetchone()
    if sesion is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if sesion["estado"] != "en_curso":
        raise HTTPException(status_code=409, detail="La sesión ya está finalizada; usa PUT para corregir el registro")
    item = conn.execute(
        "SELECT * FROM session_items WHERE id = ? AND session_id = ?", (item_id, sesion_id)
    ).fetchone()
    if item is None:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    if datos.estado == "sustituido" and catalog.get(datos.exercise_id_real) is None:
        raise HTTPException(status_code=422, detail="Ejercicio desconocido en el catálogo")

    # La ejecución registra lo realmente hecho (p. ej. adaptaciones del gimnasio):
    # no se rechaza, pero se advierte si contradice una regla dura (docs/14).
    advertencias: list[str] = []
    if datos.estado == "sustituido":
        advertencias = _advertencias_sustitucion(conn, catalog, sesion, datos.exercise_id_real)

    _guardar_estado_item(conn, item_id, datos)
    conn.commit()
    row = conn.execute("SELECT * FROM training_sessions WHERE id = ?", (sesion_id,)).fetchone()
    return {"sesion": _sesion_json(conn, row, catalog), "advertencias": advertencias}


@router.put("/api/sesiones/{sesion_id}/items/{item_id}")
def corregir_item(sesion_id: int, item_id: int, datos: ItemPatchIn, request: Request, user=Depends(usuario_actual), conn=Depends(db_conn)):
    """Corrige el registro de un ítem ya finalizado (criterio 7 de docs/14).

    La dosis real corregida sustituye a la prevista: se recalculan los puntos
    reales del ítem, y con ellos la carga de los días siguientes (criterio 4).
    """
    catalog = get_catalog(request)
    sesion = conn.execute("SELECT * FROM training_sessions WHERE id = ?", (sesion_id,)).fetchone()
    if sesion is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if sesion["estado"] == "en_curso":
        raise HTTPException(status_code=409, detail="La sesión está en curso; usa PATCH para marcar el ítem")
    item = conn.execute(
        "SELECT * FROM session_items WHERE id = ? AND session_id = ?", (item_id, sesion_id)
    ).fetchone()
    if item is None:
        raise HTTPException(status_code=404, detail="Ítem no encontrado")
    if datos.estado == "sustituido" and catalog.get(datos.exercise_id_real) is None:
        raise HTTPException(status_code=422, detail="Ejercicio desconocido en el catálogo")

    advertencias: list[str] = []
    if datos.estado == "sustituido":
        advertencias = _advertencias_sustitucion(conn, catalog, sesion, datos.exercise_id_real)

    _guardar_estado_item(conn, item_id, datos)
    item = conn.execute("SELECT * FROM session_items WHERE id = ?", (item_id,)).fetchone()
    puntos = _puntos_reales_item(item, catalog, sesion["familia"])
    conn.execute("UPDATE session_items SET puntos_reales = ? WHERE id = ?", (volcar_json(puntos), item_id))
    conn.commit()
    row = conn.execute("SELECT * FROM training_sessions WHERE id = ?", (sesion_id,)).fetchone()
    return {"sesion": _sesion_json(conn, row, catalog), "advertencias": advertencias}


def _guardar_estado_item(conn, item_id: int, datos: ItemPatchIn) -> None:
    conn.execute(
        """UPDATE session_items SET estado = ?, exercise_id_real = ?, series_real = ?,
           repeticiones_real = ?, segundos_real = ?, minutos_real = ?, carga_kg_real = ?, motivo = ?
           WHERE id = ?""",
        (
            datos.estado,
            datos.exercise_id_real,
            datos.series_real,
            datos.repeticiones_real,
            datos.segundos_real,
            datos.minutos_real,
            datos.carga_kg_real,
            datos.motivo,
            item_id,
        ),
    )


def _advertencias_sustitucion(conn, catalog: Catalog, sesion: sqlite3.Row, exercise_id_real: str) -> list[str]:
    prop_row = conn.execute("SELECT * FROM proposals WHERE id = ?", (sesion["proposal_id"],)).fetchone()
    if prop_row is None:
        return []
    from fitlosophy.generator import motivos_exclusion

    return motivos_exclusion(catalog[exercise_id_real], _prop_desde_fila(prop_row), prop_row["familia"])


def _sobre_rango(item: sqlite3.Row, ejercicio) -> bool:
    """Volumen por encima del rango prescrito (docs/12: ×1.25)."""
    p = ejercicio.prescripcion
    for campo, clave in (
        ("series_real", "series"),
        ("repeticiones_real", "repeticiones"),
        ("segundos_real", "segundos"),
        ("minutos_real", "minutos"),
    ):
        valor = item[campo]
        rango = p.get(clave)
        if valor is None or rango is None:
            continue
        maximo = rango[1] if isinstance(rango, list) else rango
        if valor > maximo:
            return True
    return False


def _puntos_reales_item(item: sqlite3.Row, catalog: Catalog, familia: str) -> dict[str, float]:
    """Impacto real del ítem (docs/14: la dosis real sustituye a la prevista)."""
    if item["estado"] == "no_realizado":
        return {}
    if item["estado"] == "sustituido":
        ejercicio = catalog[item["exercise_id_real"]]
        base = puntos_propuesta(ejercicio, familia, es_dosis_minima(familia))
    else:
        ejercicio = catalog.get(item["exercise_id"])
        base = cargar_json(item["puntos_previstos"], {})
    if ejercicio is not None and item["estado"] in ("modificado", "sustituido") and _sobre_rango(item, ejercicio):
        base = {d: p * 1.25 for d, p in base.items()}
    return base


@router.post("/api/sesiones/{sesion_id}/finalizar")
def finalizar_sesion(sesion_id: int, datos: FinalizarIn, request: Request, user=Depends(usuario_actual), conn=Depends(db_conn)):
    catalog = get_catalog(request)
    sesion = conn.execute("SELECT * FROM training_sessions WHERE id = ?", (sesion_id,)).fetchone()
    if sesion is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if sesion["estado"] != "en_curso":
        raise HTTPException(status_code=409, detail="La sesión ya está finalizada")

    # Los ítems sin marcar se dan por completados tal cual: el check es la
    # acción por defecto (docs/14, decisiones tomadas).
    conn.execute(
        "UPDATE session_items SET estado = 'completado' WHERE session_id = ? AND estado = 'pendiente'",
        (sesion_id,),
    )
    totales: dict[str, float] = {}
    for item in conn.execute("SELECT * FROM session_items WHERE session_id = ?", (sesion_id,)).fetchall():
        puntos = _puntos_reales_item(item, catalog, sesion["familia"])
        conn.execute("UPDATE session_items SET puntos_reales = ? WHERE id = ?", (volcar_json(puntos), item["id"]))
        for d, p in puntos.items():
            totales[d] = totales.get(d, 0.0) + p

    ahora = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        "UPDATE training_sessions SET estado = 'finalizada', rpe_real = ?, finalizada_at = ? WHERE id = ?",
        (datos.rpe_real, ahora, sesion_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM training_sessions WHERE id = ?", (sesion_id,)).fetchone()
    return {"sesion": _sesion_json(conn, row, catalog), "puntos_sesion_real": totales}


# --- 4. Cierre (respuesta posterior, docs/12) -------------------------------------------


@router.post("/api/sesiones/{sesion_id}/cierre", status_code=201)
def cerrar_sesion(sesion_id: int, datos: CierreIn, request: Request, user=Depends(usuario_actual), conn=Depends(db_conn)):
    sesion = conn.execute("SELECT * FROM training_sessions WHERE id = ?", (sesion_id,)).fetchone()
    if sesion is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if sesion["estado"] not in ("finalizada", "cerrada"):
        raise HTTPException(status_code=409, detail="Finaliza la sesión antes del cierre")
    existente = conn.execute("SELECT id FROM session_closures WHERE session_id = ?", (sesion_id,)).fetchone()
    if existente is not None:
        raise HTTPException(status_code=409, detail="La sesión ya tiene cierre; usa PUT para corregirlo")

    molestias = [m.model_dump() for m in datos.molestias]
    congeladas, desconocidas = dimensiones_de_molestias(molestias)
    conn.execute(
        "INSERT INTO session_closures (session_id, sensacion, molestias, dimensiones_congeladas, created_at) VALUES (?, ?, ?, ?, ?)",
        (
            sesion_id,
            datos.sensacion,
            volcar_json(molestias),
            volcar_json(congeladas),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.execute("UPDATE training_sessions SET estado = 'cerrada' WHERE id = ?", (sesion_id,))
    conn.commit()
    respuesta = {"dimensiones_congeladas": congeladas}
    if desconocidas:
        respuesta["zonas_sin_mapear"] = desconocidas
        respuesta["nota"] = "Zonas sin mapeo a dimensión de carga: no congelan ventana; revísalas manualmente."
    return respuesta


# --- 5. Historial y correcciones (criterio 7) -------------------------------------------


def _fecha_de(row_fecha: str) -> str:
    return row_fecha[:10]


@router.get("/api/historial")
def historial_lista(request: Request, dias: int = 30, user=Depends(usuario_actual), conn=Depends(db_conn)):
    hoy = date.today()
    salida = []
    for i in range(dias):
        fecha = (hoy - timedelta(days=i)).isoformat()
        sesiones = conn.execute(
            "SELECT id, familia, estado FROM training_sessions WHERE substr(fecha, 1, 10) = ?", (fecha,)
        ).fetchall()
        bjjs = conn.execute(
            "SELECT id, clasificacion, duracion_minutos FROM bjj_records WHERE substr(fecha, 1, 10) = ?", (fecha,)
        ).fetchall()
        estado = conn.execute(
            "SELECT id FROM daily_states WHERE substr(fecha, 1, 10) = ?", (fecha,)
        ).fetchone()

        tipos: list[str] = []
        for s in sesiones:
            tipo = "recuperacion" if s["familia"] == "C" else "fisica"
            if tipo not in tipos:
                tipos.append(tipo)
        if bjjs:
            tipos.append("bjj")
        if not sesiones and not bjjs:
            tipos.append("descanso" if estado else "sin_registro")

        salida.append(
            {
                "fecha": fecha,
                "tipos": tipos,
                "sesiones": [dict(s) for s in sesiones],
                "bjj": [dict(b) for b in bjjs],
                "estado_diario": estado is not None,
            }
        )
    return {"dias": salida}


@router.get("/api/historial/{fecha}")
def historial_detalle(fecha: str, request: Request, user=Depends(usuario_actual), conn=Depends(db_conn)):
    try:
        date.fromisoformat(fecha)
    except ValueError:
        raise HTTPException(status_code=422, detail="Fecha inválida (formato YYYY-MM-DD)")
    catalog = get_catalog(request)

    estados = conn.execute(
        "SELECT * FROM daily_states WHERE substr(fecha, 1, 10) = ? ORDER BY id", (fecha,)
    ).fetchall()
    # Las propuestas descartadas y las sesiones canceladas no se muestran: son
    # ruido de haber redeclarado el estado, no lo que pasó ese día (docs/14).
    propuestas = conn.execute(
        "SELECT * FROM proposals WHERE substr(fecha, 1, 10) = ? AND estado != 'descartada' ORDER BY id",
        (fecha,),
    ).fetchall()
    sesiones = conn.execute(
        "SELECT * FROM training_sessions WHERE substr(fecha, 1, 10) = ? AND estado != 'cancelada' ORDER BY id",
        (fecha,),
    ).fetchall()
    bjjs = conn.execute(
        "SELECT * FROM bjj_records WHERE substr(fecha, 1, 10) = ? ORDER BY id", (fecha,)
    ).fetchall()

    return {
        "fecha": fecha,
        "estados_diarios": [
            {
                "id": e["id"],
                "recuperacion": e["recuperacion"],
                "dolor": e["dolor"],
                "zona_dolor": e["zona_dolor"],
                "bjj_disponible": e["bjj_disponible"],
                "tipo_bjj": e["tipo_bjj"],
                "limitacion": e["limitacion"],
                "sueno": e["sueno"],
                "tiempo_disponible": e["tiempo_disponible"],
                "preferencia": e["preferencia"],
                "circunstancias": e["circunstancias"],
                "material_disponible": cargar_json(e["material_disponible"], None),
            }
            for e in estados
        ],
        "propuestas": [_propuesta_json(p, catalog) for p in propuestas],
        "sesiones": [_sesion_json(conn, s, catalog) for s in sesiones],
        "bjj": [
            {
                "id": b["id"],
                "fecha": b["fecha"],
                "clasificacion": b["clasificacion"],
                "duracion_minutos": b["duracion_minutos"],
                "fatiga_agarre": bool(b["fatiga_agarre"]),
                "intensidad_percibida": b["intensidad_percibida"],
                "notas": b["notas"],
                "estimado": bool(b["estimado"]),
            }
            for b in bjjs
        ],
    }


@router.post("/api/bjj", status_code=201)
def registrar_bjj(datos: BjjIn, request: Request, user=Depends(usuario_actual), conn=Depends(db_conn)):
    fecha = datos.fecha or datetime.now()
    cur = conn.execute(
        """INSERT INTO bjj_records (fecha, clasificacion, duracion_minutos, fatiga_agarre,
           intensidad_percibida, notas, estimado, created_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)""",
        (
            fecha.isoformat(timespec="seconds"),
            datos.clasificacion,
            datos.duracion_minutos,
            int(datos.fatiga_agarre),
            datos.intensidad_percibida,
            datos.notas,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    return {"id": int(cur.lastrowid)}


@router.put("/api/bjj/{registro_id}")
def corregir_bjj(registro_id: int, datos: BjjPut, user=Depends(usuario_actual), conn=Depends(db_conn)):
    row = conn.execute("SELECT * FROM bjj_records WHERE id = ?", (registro_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Registro de BJJ no encontrado")
    campos = {
        "clasificacion": datos.clasificacion,
        "duracion_minutos": datos.duracion_minutos,
        "fecha": datos.fecha.isoformat(timespec="seconds") if datos.fecha else None,
        "fatiga_agarre": None if datos.fatiga_agarre is None else int(datos.fatiga_agarre),
        "intensidad_percibida": datos.intensidad_percibida,
        "notas": datos.notas,
    }
    for campo, valor in campos.items():
        if valor is not None:
            conn.execute(f"UPDATE bjj_records SET {campo} = ? WHERE id = ?", (valor, registro_id))
    conn.commit()
    return {"id": registro_id, "detalle": "Registro corregido"}


@router.put("/api/sesiones/{sesion_id}")
def corregir_sesion(sesion_id: int, datos: SesionPut, user=Depends(usuario_actual), conn=Depends(db_conn)):
    row = conn.execute("SELECT * FROM training_sessions WHERE id = ?", (sesion_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if datos.rpe_real is not None:
        conn.execute("UPDATE training_sessions SET rpe_real = ? WHERE id = ?", (datos.rpe_real, sesion_id))
    if datos.fecha is not None:
        conn.execute("UPDATE training_sessions SET fecha = ? WHERE id = ?", (datos.fecha.isoformat(timespec="seconds"), sesion_id))
    conn.commit()
    return {"id": sesion_id, "detalle": "Sesión corregida"}


@router.put("/api/sesiones/{sesion_id}/cierre")
def corregir_cierre(sesion_id: int, datos: CierrePut, user=Depends(usuario_actual), conn=Depends(db_conn)):
    row = conn.execute("SELECT * FROM session_closures WHERE session_id = ?", (sesion_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="La sesión no tiene cierre registrado")
    sensacion = datos.sensacion or row["sensacion"]
    molestias = (
        [m.model_dump() for m in datos.molestias]
        if datos.molestias is not None
        else cargar_json(row["molestias"], [])
    )
    congeladas, _ = dimensiones_de_molestias(molestias)
    conn.execute(
        "UPDATE session_closures SET sensacion = ?, molestias = ?, dimensiones_congeladas = ? WHERE session_id = ?",
        (sensacion, volcar_json(molestias), volcar_json(congeladas), sesion_id),
    )
    conn.commit()
    return {"id": sesion_id, "dimensiones_congeladas": congeladas}


# --- 6. Perfil ----------------------------------------------------------------------------


@router.get("/api/perfil")
def obtener_perfil(user=Depends(usuario_actual), conn=Depends(db_conn)):
    fila = conn.execute("SELECT data, updated_at FROM profile WHERE id = 1").fetchone()
    if fila is None:
        raise HTTPException(status_code=404, detail="Perfil no inicializado")
    data = cargar_json(fila["data"], {})
    perfil = perfil_desde_dict(data)
    return {"data": data, "material": sorted(perfil.material), "updated_at": fila["updated_at"]}


@router.put("/api/perfil")
def actualizar_perfil(datos: PerfilPut, user=Depends(usuario_actual), conn=Depends(db_conn)):
    if not isinstance(datos.data, dict) or not datos.data:
        raise HTTPException(status_code=422, detail="El perfil debe ser un objeto con la forma de data/perfil.yaml")
    conn.execute(
        "INSERT INTO profile (id, data, updated_at) VALUES (1, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET data = excluded.data, updated_at = excluded.updated_at",
        (volcar_json(datos.data), datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    return {"detalle": "Perfil actualizado"}


# --- Catálogo de ejercicios (selector de sustituciones) ------------------------------------------


@router.get("/api/ejercicios")
def listar_ejercicios(request: Request, user=Depends(usuario_actual)):
    catalog = get_catalog(request)
    return {"ejercicios": [{"id": e.id, "nombre": e.nombre, "patron": e.patron} for e in catalog]}


# --- Exportación (portabilidad, docs/14) -----------------------------------------------------


@router.get("/api/export")
def exportar(user=Depends(usuario_actual), conn=Depends(db_conn)):
    tablas = [
        "daily_states",
        "proposals",
        "training_sessions",
        "session_items",
        "session_closures",
        "bjj_records",
        "profile",
    ]
    volcado = {
        t: [dict(fila) for fila in conn.execute(f"SELECT * FROM {t}").fetchall()] for t in tablas
    }
    return {
        "aplicacion": "fitlosophy",
        "version": "0.1.0",
        "exportado_en": datetime.now().isoformat(timespec="seconds"),
        "datos": volcado,
    }
