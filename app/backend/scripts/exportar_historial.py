"""Exporta el historial de entrenamiento de **un** usuario a CSV y Markdown.

El historial es dato de salud de cada atleta, así que el script nunca vuelca la
tabla entera: recibe el nombre de usuario y filtra por `user_id` (docs/14,
criterio 10). Escribe por defecto en `temp/historico/`, que está ignorado por
git, porque un export de la BD no se versiona (`.gitignore`: ni la base ni sus
copias).

Seis ficheros, todos regenerables:

- `ejercicios.csv`: una fila por ejercicio de cada sesión, en formato largo
  (contexto del día y de la sesión repetido en cada fila).
- `sesiones.csv`: una fila por sesión, con los puntos previstos y reales
  sumados por dimensión.
- `actividades.csv`: una fila por actividad externa (BJJ, grappling u otra),
  con su carga en UA y los datos del registro de BJJ enlazado.
- `bienestar.csv`: una fila por revisión matutina, con los seis indicadores.
- `bjj.csv`: una fila por registro de BJJ, venga del formulario manual o de una
  actividad externa (`origen`).
- `historico.md`: diario por días. Cada fecha junta el bienestar de la mañana,
  las actividades externas, los registros manuales de BJJ y las sesiones del
  generador con su tabla de ejercicios.

`--solo-cerradas` afecta **solo a las sesiones** (y por tanto a
`sesiones.csv`, `ejercicios.csv` y a los bloques de sesión del diario): las
actividades, el bienestar y el BJJ se exportan completos, porque no son
sesiones y ocultarlos dejaría el historial cojo.

Uso:
    cd app/backend
    ./.venv/bin/python scripts/exportar_historial.py --usuario paulo
    ./.venv/bin/python scripts/exportar_historial.py --usuario paulo --solo-cerradas
    ./.venv/bin/python scripts/exportar_historial.py --usuario paulo --salida /tmp/analisis
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

from _comun import RAIZ, abrir_bd, ejecutar

from fitlosophy.catalog import load_default_catalog  # noqa: E402
from fitlosophy_api.db import cargar_json  # noqa: E402

SALIDA_POR_DEFECTO = RAIZ.parent.parent / "temp" / "historico"

DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")

# No es dato de entrenamiento, pero sin él las fechas son ilegibles.
SESIONES_SQL = """
SELECT ts.id, ts.fecha, ts.familia, ts.estado, ts.rpe_real, ts.finalizada_at,
       p.techo, p.reducida, p.duracion_estimada_min, p.rpe_previsto, p.reglas,
       p.d3, p.d4, p.d5,
       ds.recuperacion, ds.dolor, ds.zona_dolor, ds.bjj_disponible, ds.tipo_bjj,
       ds.limitacion, ds.sueno, ds.tiempo_disponible, ds.preferencia,
       ds.circunstancias, ds.material_disponible,
       sc.sensacion, sc.molestias, sc.dimensiones_congeladas
  FROM training_sessions ts
  LEFT JOIN proposals p ON p.id = ts.proposal_id
  LEFT JOIN daily_states ds ON ds.id = p.daily_state_id
  LEFT JOIN session_closures sc ON sc.session_id = ts.id
 WHERE ts.user_id = ?{filtro}
 ORDER BY ts.fecha, ts.id
"""

ITEMS_SQL = """
SELECT si.*
  FROM session_items si
  JOIN training_sessions ts ON ts.id = si.session_id
 WHERE ts.user_id = ?{filtro}
 ORDER BY si.session_id, si.id
"""

ACTIVIDADES_SQL = """
SELECT ea.id, ea.fecha, ea.tipo, ea.nombre, ea.duracion_minutos, ea.rpe,
       ea.combates, ea.observaciones, ea.created_at, ea.updated_at,
       b.id AS bjj_id, b.clasificacion, b.intensidad_percibida, b.fatiga_agarre
  FROM external_activities ea
  LEFT JOIN bjj_records b ON b.external_activity_id = ea.id AND b.user_id = ea.user_id
 WHERE ea.user_id = ?
 ORDER BY ea.fecha, ea.id
"""

BIENESTAR_SQL = """
SELECT * FROM morning_checkins WHERE user_id = ? ORDER BY fecha
"""

BJJ_SQL = """
SELECT *, CASE WHEN external_activity_id IS NULL THEN 'manual' ELSE 'externa' END AS origen
  FROM bjj_records WHERE user_id = ?
 ORDER BY fecha, id
"""


def _usuario(conn, nombre: str) -> int:
    fila = conn.execute("SELECT id FROM users WHERE username = ?", (nombre,)).fetchone()
    if fila is None:
        disponibles = [r["username"] for r in conn.execute("SELECT username FROM users ORDER BY id")]
        raise SystemExit(f"No existe el usuario «{nombre}». En esta BD hay: {', '.join(disponibles)}")
    return fila["id"]


def _lista(valor) -> str:
    """Lista JSON de la BD o lista de Python del catálogo a texto plano de una
    línea, para que la celda del CSV no lleve saltos."""
    if isinstance(valor, (list, tuple)):
        return "|".join(str(d) for d in valor)
    datos = cargar_json(valor, [])
    if not isinstance(datos, list):
        return str(valor or "")
    return "|".join(str(d) for d in datos)


def _dia(fecha: str) -> str:
    return DIAS[datetime.strptime(fecha[:10], "%Y-%m-%d").weekday()]


def _real(item) -> str:
    """Dosis realmente registrada, en texto compacto ('' si no se anotó)."""
    partes = []
    if item["series_real"] and item["repeticiones_real"]:
        partes.append(f"{item['series_real']}×{item['repeticiones_real']}")
    elif item["repeticiones_real"]:
        partes.append(f"{item['repeticiones_real']} reps")
    if item["segundos_real"]:
        partes.append(f"{item['segundos_real']} s")
    if item["minutos_real"]:
        partes.append(f"{item['minutos_real']} min")
    return " ".join(partes)


def _filas_sesion(sesion, items, dimensiones) -> dict:
    """Una fila por sesión, con los puntos sumados por dimensión."""
    previstos = {d: 0.0 for d in dimensiones}
    reales = {d: 0.0 for d in dimensiones}
    for it in items:
        for destino, bruto in ((previstos, it["puntos_previstos"]), (reales, it["puntos_reales"])):
            for dim, valor in cargar_json(bruto, {}).items():
                destino[dim] = destino.get(dim, 0.0) + float(valor)
    fecha = sesion["fecha"][:10]
    fila = {
        "sesion_id": sesion["id"],
        "fecha": fecha,
        "dia_semana": _dia(fecha),
        "hora": sesion["fecha"][11:16],
        "familia": sesion["familia"],
        "techo": sesion["techo"] or "",
        "reducida": "si" if sesion["reducida"] else "no",
        "estado": sesion["estado"],
        "rpe_previsto": sesion["rpe_previsto"] or "",
        "rpe_real": sesion["rpe_real"] if sesion["rpe_real"] is not None else "",
        "duracion_estimada_min": sesion["duracion_estimada_min"] or "",
        "reglas": _lista(sesion["reglas"]),
        "d3": sesion["d3"] or 0,
        "d4": sesion["d4"] or 0,
        "d5": sesion["d5"] or 0,
        "sensacion": sesion["sensacion"] or "",
        "molestias": _lista(sesion["molestias"]),
        "dimensiones_congeladas": _lista(sesion["dimensiones_congeladas"]),
        "recuperacion": sesion["recuperacion"] or "",
        "dolor": sesion["dolor"] if sesion["dolor"] is not None else "",
        "zona_dolor": sesion["zona_dolor"] or "",
        "bjj_disponible": sesion["bjj_disponible"] or "",
        "tipo_bjj": sesion["tipo_bjj"] or "",
        "sueno": sesion["sueno"] if sesion["sueno"] is not None else "",
        "tiempo_disponible": sesion["tiempo_disponible"] or "",
        "preferencia": sesion["preferencia"] or "",
        "limitacion": sesion["limitacion"] or "",
        "circunstancias": sesion["circunstancias"] or "",
        "material_disponible": _lista(sesion["material_disponible"]),
        "n_items": len(items),
        "n_completados": sum(1 for i in items if i["estado"] == "completado"),
        "n_sustituidos": sum(1 for i in items if i["estado"] == "sustituido"),
        "n_pendientes": sum(1 for i in items if i["estado"] == "pendiente"),
    }
    for d in dimensiones:
        fila[f"previsto_{d}"] = round(previstos.get(d, 0.0), 2)
        fila[f"real_{d}"] = round(reales.get(d, 0.0), 2)
    return fila


def _filas_ejercicios(sesion, items, catalog, dimensiones) -> list[dict]:
    """Una fila por ejercicio, con el contexto de su sesión repetido."""
    fecha = sesion["fecha"][:10]
    contexto = {
        "sesion_id": sesion["id"],
        "fecha": fecha,
        "dia_semana": _dia(fecha),
        "familia": sesion["familia"],
        "estado_sesion": sesion["estado"],
        "rpe_sesion": sesion["rpe_real"] if sesion["rpe_real"] is not None else "",
        "sensacion": sesion["sensacion"] or "",
        "recuperacion": sesion["recuperacion"] or "",
        "dolor": sesion["dolor"] if sesion["dolor"] is not None else "",
        "zona_dolor": sesion["zona_dolor"] or "",
        "bjj_disponible": sesion["bjj_disponible"] or "",
        "tipo_bjj": sesion["tipo_bjj"] or "",
        "sueno": sesion["sueno"] if sesion["sueno"] is not None else "",
        "tiempo_disponible": sesion["tiempo_disponible"] or "",
        "preferencia": sesion["preferencia"] or "",
        "material_disponible": _lista(sesion["material_disponible"]),
    }
    filas = []
    for orden, it in enumerate(items, start=1):
        ej = catalog.get(it["exercise_id"])
        real = catalog.get(it["exercise_id_real"]) if it["exercise_id_real"] else None
        fila = dict(contexto)
        fila.update(
            {
                "orden": orden,
                "bloque": it["bloque"],
                "estado_item": it["estado"],
                "ejercicio_id": it["exercise_id"],
                "ejercicio": ej.nombre if ej else it["exercise_id"],
                "patron": ej.patron if ej else "",
                "impacto_lumbar": ej.impacto_lumbar if ej else "",
                "intencion": ej.intencion if ej else "",
                "material": _lista(list(ej.material)) if ej else "",
                "dosis_prevista": it["dosis"],
                "series_real": it["series_real"] if it["series_real"] is not None else "",
                "repeticiones_real": it["repeticiones_real"] if it["repeticiones_real"] is not None else "",
                "segundos_real": it["segundos_real"] if it["segundos_real"] is not None else "",
                "minutos_real": it["minutos_real"] if it["minutos_real"] is not None else "",
                "carga_kg_real": it["carga_kg_real"] if it["carga_kg_real"] is not None else "",
                "dosis_real": _real(it),
                "ejercicio_real_id": it["exercise_id_real"] or "",
                "ejercicio_real": real.nombre if real else "",
                "motivo": it["motivo"] or "",
                "justificacion": it["justificacion"] or "",
            }
        )
        previstos = cargar_json(it["puntos_previstos"], {})
        reales = cargar_json(it["puntos_reales"], {})
        for d in dimensiones:
            fila[f"previsto_{d}"] = previstos.get(d, "")
            fila[f"real_{d}"] = reales.get(d, "")
        filas.append(fila)
    return filas


def _filas_actividades(actividades) -> list[dict]:
    """Una fila por actividad externa. `carga_ua` es duración × RPE (docs)."""
    filas = []
    for a in actividades:
        fila = {
            "id": a["id"],
            "fecha": a["fecha"],
            "dia_semana": _dia(a["fecha"]),
            "tipo": a["tipo"],
            "nombre": a["nombre"] or "",
            "duracion_minutos": a["duracion_minutos"],
            "rpe": a["rpe"],
            "carga_ua": a["duracion_minutos"] * a["rpe"],
            # NULL = no informado, distinto de 0 (especificación §4.6).
            "combates": a["combates"] if a["combates"] is not None else "",
            "observaciones": a["observaciones"] or "",
            "bjj_clasificacion": a["clasificacion"] or "",
            "bjj_intensidad": a["intensidad_percibida"] if a["intensidad_percibida"] is not None else "",
            "bjj_fatiga_agarre": ("si" if a["fatiga_agarre"] else "no") if a["bjj_id"] else "",
            "created_at": a["created_at"],
            "updated_at": a["updated_at"],
        }
        filas.append(fila)
    return filas


def _filas_bienestar(registros) -> list[dict]:
    """Una fila por revisión matutina. Vacío en el CSV = no valorado."""
    def valor(r, clave):
        return r[clave] if r[clave] is not None else ""

    return [
        {
            "fecha": r["fecha"],
            "dia_semana": _dia(r["fecha"]),
            "calidad_sueno": valor(r, "calidad_sueno"),
            "recuperacion_fisica": valor(r, "recuperacion_fisica"),
            "molestias_fisicas": valor(r, "molestias_fisicas"),
            "zonas_molestias": _lista(r["zonas_molestias"]),
            "energia_fisica": valor(r, "energia_fisica"),
            "claridad_mental": valor(r, "claridad_mental"),
            "estres_previsto": valor(r, "estres_previsto"),
            "observaciones": r["observaciones"] or "",
            "updated_at": r["updated_at"],
        }
        for r in registros
    ]


def _filas_bjj(registros) -> list[dict]:
    """Una fila por registro de BJJ, con su origen (manual o actividad externa)."""
    return [
        {
            "id": r["id"],
            "fecha": r["fecha"][:10],
            "dia_semana": _dia(r["fecha"]),
            "origen": r["origen"],
            "clasificacion": r["clasificacion"],
            "duracion_minutos": r["duracion_minutos"],
            "intensidad_percibida": r["intensidad_percibida"] if r["intensidad_percibida"] is not None else "",
            "fatiga_agarre": "si" if r["fatiga_agarre"] else "no",
            "estimado": "si" if r["estimado"] else "no",
            "notas": r["notas"] or "",
            "external_activity_id": r["external_activity_id"] if r["external_activity_id"] is not None else "",
            "created_at": r["created_at"],
        }
        for r in registros
    ]


def _escribir_csv(ruta: Path, filas: list[dict]) -> None:
    if not filas:
        ruta.write_text("", encoding="utf-8")
        return
    with ruta.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        escritor.writeheader()
        escritor.writerows(filas)


def _carga_ua(actividades) -> int:
    return sum(a["duracion_minutos"] * a["rpe"] for a in actividades)


def _bienestar_linea(r) -> str:
    def v(clave):
        return r[clave] if r[clave] is not None else "sin valorar"

    zonas = _lista(r["zonas_molestias"])
    return (
        f"sueño {v('calidad_sueno')} · recuperación {v('recuperacion_fisica')} · "
        f"molestias {v('molestias_fisicas')}"
        + (f" ({zonas})" if zonas else "")
        + f" · energía {v('energia_fisica')} · claridad {v('claridad_mental')} · "
        f"estrés {v('estres_previsto')}"
        + (f" · obs.: {r['observaciones']}" if r["observaciones"] else "")
    )


def _actividad_linea(a) -> str:
    nombre = a["nombre"] or (a["tipo"] if a["tipo"] != "otra" else "otra")
    partes = [
        f"{nombre} · {a['duracion_minutos']} min · RPE {a['rpe']} · "
        f"{a['duracion_minutos'] * a['rpe']} UA"
    ]
    if a["combates"] is not None:
        partes.append(f"combates {a['combates']}")
    if a["bjj_id"]:
        partes.append(
            f"BJJ {a['clasificacion']} (int {a['intensidad_percibida']}, "
            f"agarre {'sí' if a['fatiga_agarre'] else 'no'})"
        )
    if a["observaciones"]:
        partes.append(a["observaciones"])
    return " · ".join(partes)


def _bloque_sesion(s, items, catalog) -> list[str]:
    """Tabla de una sesión con su dosis, peso y desviaciones."""
    lineas = [
        f"### Sesión {s['familia']} · {s['estado']} · "
        f"RPE {s['rpe_real'] if s['rpe_real'] is not None else '—'} · "
        f"{len(items)} ejercicios · duración estimada {s['duracion_estimada_min'] or '—'} min",
        "",
        f"- Estado del día: recuperación {s['recuperacion'] or '—'} · "
        f"dolor {s['dolor'] if s['dolor'] is not None else '—'}"
        + (f" ({s['zona_dolor']})" if s["zona_dolor"] else "")
        + f" · BJJ {s['bjj_disponible'] or '—'}"
        + (f" ({s['tipo_bjj']})" if s["tipo_bjj"] else ""),
        f"- Sensación: {s['sensacion'] or '—'} · molestias: "
        f"{_lista(s['molestias']) or 'ninguna'}",
        "",
        "| Bloque | Ejercicio | Dosis del día | Peso (kg) | Desviación |",
        "|---|---|---|---|---|",
    ]
    for it in items:
        ej = catalog.get(it["exercise_id"])
        real_ej = catalog.get(it["exercise_id_real"]) if it["exercise_id_real"] else None
        nombre = ej.nombre if ej else it["exercise_id"]
        if real_ej is not None:
            nombre += f" → {real_ej.nombre}"
        if it["estado"] == "pendiente":
            desviacion = "no realizado"
        elif it["estado"] == "sustituido" and real_ej is not None:
            desviacion = f"sustituido por {real_ej.nombre}"
        elif _real(it):
            desviacion = f"modificado: {_real(it)}"
        else:
            desviacion = "—"
        if it["motivo"]:
            desviacion += f" ({it['motivo']})"
        peso = it["carga_kg_real"] if it["carga_kg_real"] is not None else "—"
        lineas.append(f"| {it['bloque']} | {nombre} | {it['dosis']} | {peso} | {desviacion} |")
    lineas.append("")
    return lineas


def _markdown(usuario, sesiones, por_sesion, actividades, checkins, bjj_manual, catalog) -> str:
    """Diario por días: bienestar de la mañana, actividad externa, BJJ manual y
    sesiones del generador, en orden cronológico.

    Marcar el check sin abrir el modal significa «se hizo tal cual» (docs/14),
    así que la dosis del día *es* lo realizado: la columna «Desviación» solo
    lleva algo cuando se registró una modificación o una sustitución.
    """
    por_fecha: dict[str, dict] = {}
    for s in sesiones:
        por_fecha.setdefault(s["fecha"][:10], {"sesiones": [], "actividades": [], "bjj": [], "bienestar": None})
        por_fecha[s["fecha"][:10]]["sesiones"].append(s)
    for a in actividades:
        por_fecha.setdefault(a["fecha"], {"sesiones": [], "actividades": [], "bjj": [], "bienestar": None})
        por_fecha[a["fecha"]]["actividades"].append(a)
    for r in checkins:
        entrada = por_fecha.setdefault(
            r["fecha"], {"sesiones": [], "actividades": [], "bjj": [], "bienestar": None}
        )
        entrada["bienestar"] = r
    for b in bjj_manual:
        clave = b["fecha"][:10]
        por_fecha.setdefault(clave, {"sesiones": [], "actividades": [], "bjj": [], "bienestar": None})
        por_fecha[clave]["bjj"].append(b)

    fechas = sorted(por_fecha)
    con_registro = len(fechas)
    total_dias = 0
    vacios = 0
    if fechas:
        desde = datetime.strptime(fechas[0], "%Y-%m-%d").date()
        hasta = datetime.strptime(fechas[-1], "%Y-%m-%d").date()
        total_dias = (hasta - desde).days + 1
        vacios = total_dias - con_registro

    lineas = [
        f"# Histórico de entrenamientos — {usuario}",
        "",
        f"Exportado el {datetime.now():%Y-%m-%d %H:%M}. "
        + (f"{fechas[0]} → {fechas[-1]} ({total_dias} días)." if fechas else "Sin registros."),
        "",
        "## Resumen",
        "",
        f"- Sesiones del generador: **{len(sesiones)}** "
        f"({sum(1 for s in sesiones if s['estado'] == 'cerrada')} cerradas), "
        f"{sum(len(v) for v in por_sesion.values())} ejercicios.",
        f"- Actividades externas: **{len(actividades)}** · "
        f"{_carga_ua(actividades)} UA · "
        f"BJJ/grappling enlazados: {sum(1 for a in actividades if a['bjj_id'])}.",
        f"- Registros de BJJ: **{len(bjj_manual) + sum(1 for a in actividades if a['bjj_id'])}** "
        f"({len(bjj_manual)} manuales, {sum(1 for a in actividades if a['bjj_id'])} desde actividad externa).",
        f"- Revisiones matutinas: **{len(checkins)}**.",
        f"- Días con algún registro: **{con_registro} de {total_dias}** · días vacíos: {vacios}.",
        "",
        "La «dosis del día» equivale a lo realizado: marcar el check sin "
        "desviación significa «tal cual» (docs/14). «Modificado» y "
        "«sustituido» aparecen solo cuando se registraron como tales. La carga "
        "en UA (duración × RPE) solo existe para actividades externas: la de "
        "las sesiones es una estimación.",
        "",
    ]

    for fecha in fechas:
        dia = por_fecha[fecha]
        lineas += [f"## {fecha} ({_dia(fecha)})", ""]
        if dia["bienestar"] is not None:
            lineas += [f"**Bienestar:** {_bienestar_linea(dia['bienestar'])}", ""]
        else:
            lineas += ["**Bienestar:** sin revisión matutina", ""]
        for a in dia["actividades"]:
            lineas.append(f"**Actividad externa:** {_actividad_linea(a)}")
        for b in dia["bjj"]:
            nota = f" · {b['notas']}" if b["notas"] else ""
            lineas.append(
                f"**BJJ manual:** {b['clasificacion']} · {b['duracion_minutos']} min · "
                f"intensidad {b['intensidad_percibida'] if b['intensidad_percibida'] is not None else '—'} · "
                f"agarre {'sí' if b['fatiga_agarre'] else 'no'}{nota}"
            )
        if dia["actividades"] or dia["bjj"]:
            lineas.append("")
        for s in dia["sesiones"]:
            lineas += _bloque_sesion(s, por_sesion.get(s["id"], []), catalog)
        if lineas and lineas[-1] != "":
            lineas.append("")

    return "\n".join(lineas)


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta el historial de un usuario a CSV/Markdown.")
    parser.add_argument("--usuario", required=True, help="nombre de usuario (`username`)")
    parser.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO, help="directorio de salida")
    parser.add_argument(
        "--solo-cerradas",
        action="store_true",
        help="exporta solo las sesiones cerradas (actividades, bienestar y BJJ van completos)",
    )
    args = parser.parse_args()

    conn, ruta_bd = abrir_bd()
    user_id = _usuario(conn, args.usuario)
    catalog = load_default_catalog()
    dimensiones = list(catalog.valores["dimensiones"])

    filtro = " AND ts.estado = 'cerrada'" if args.solo_cerradas else ""
    sesiones = conn.execute(SESIONES_SQL.format(filtro=filtro), (user_id,)).fetchall()
    items = conn.execute(ITEMS_SQL.format(filtro=filtro), (user_id,)).fetchall()
    actividades = conn.execute(ACTIVIDADES_SQL, (user_id,)).fetchall()
    checkins = conn.execute(BIENESTAR_SQL, (user_id,)).fetchall()
    bjj = conn.execute(BJJ_SQL, (user_id,)).fetchall()
    bjj_manual = [b for b in bjj if b["external_activity_id"] is None]

    if not (sesiones or actividades or checkins or bjj):
        print(f"El usuario «{args.usuario}» no tiene ningún registro en {ruta_bd}.")
        return 0

    por_sesion: dict[int, list] = {}
    for it in items:
        por_sesion.setdefault(it["session_id"], []).append(it)

    filas_sesion = [_filas_sesion(s, por_sesion.get(s["id"], []), dimensiones) for s in sesiones]
    filas_ejercicios = [
        fila for s in sesiones for fila in _filas_ejercicios(s, por_sesion.get(s["id"], []), catalog, dimensiones)
    ]
    filas_actividades = _filas_actividades(actividades)
    filas_bienestar = _filas_bienestar(checkins)
    filas_bjj = _filas_bjj(bjj)

    args.salida.mkdir(parents=True, exist_ok=True)
    _escribir_csv(args.salida / "sesiones.csv", filas_sesion)
    _escribir_csv(args.salida / "ejercicios.csv", filas_ejercicios)
    _escribir_csv(args.salida / "actividades.csv", filas_actividades)
    _escribir_csv(args.salida / "bienestar.csv", filas_bienestar)
    _escribir_csv(args.salida / "bjj.csv", filas_bjj)
    (args.salida / "historico.md").write_text(
        _markdown(
            args.usuario, sesiones, por_sesion, actividades, checkins, bjj_manual, catalog
        ),
        encoding="utf-8",
    )

    completados = sum(1 for f in filas_ejercicios if f["estado_item"] == "completado")
    alcance = "solo sesiones cerradas" if args.solo_cerradas else "todas las sesiones"
    print(f"Exportado el historial de «{args.usuario}» desde {ruta_bd} ({alcance}):")
    print(
        f"  {len(sesiones)} sesiones ({sum(1 for s in sesiones if s['estado'] == 'cerrada')} cerradas), "
        f"{len(filas_ejercicios)} ejercicios ({completados} completados)"
    )
    print(f"  {len(actividades)} actividades externas ({_carga_ua(actividades)} UA), "
          f"{len(bjj)} registros de BJJ, {len(checkins)} revisiones matutinas")
    semanas = sorted({a["fecha"][:7] for a in actividades})
    print(f"  meses con actividad externa: {', '.join(semanas) if semanas else '—'}")
    for nombre in (
        "sesiones.csv",
        "ejercicios.csv",
        "actividades.csv",
        "bienestar.csv",
        "bjj.csv",
        "historico.md",
    ):
        print(f"  {args.salida / nombre}")
    print("\nAviso: es un export de datos de salud; no lo muevas a una ruta versionada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
