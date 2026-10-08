"""Exporta el historial de entrenamiento de **un** usuario a CSV y Markdown.

El historial es dato de salud de cada atleta, así que el script nunca vuelca la
tabla entera: recibe el nombre de usuario y filtra por `user_id` (docs/14,
criterio 10). Escribe por defecto en `temp/historico/`, que está ignorado por
git, porque un export de la BD no se versiona (`.gitignore`: ni la base ni sus
copias).

Tres ficheros, todos regenerables:

- `ejercicios.csv`: una fila por ejercicio de cada sesión, en formato largo
  (contexto del día y de la sesión repetido en cada fila). Es el fichero para
  analizar.
- `sesiones.csv`: una fila por sesión, con los puntos previstos y reales
  sumados por dimensión.
- `historico.md`: lo mismo que `ejercicios.csv` pero legible de un vistazo.

Uso:
    cd app/backend
    ./.venv/bin/python scripts/exportar_historial.py --usuario paulo
    ./.venv/bin/python scripts/exportar_historial.py --usuario paulo --salida /tmp/analisis
"""

from __future__ import annotations

import argparse
import csv
import sys
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
 WHERE ts.user_id = ?
 ORDER BY ts.fecha, ts.id
"""

ITEMS_SQL = """
SELECT si.*
  FROM session_items si
  JOIN training_sessions ts ON ts.id = si.session_id
 WHERE ts.user_id = ?
 ORDER BY si.session_id, si.id
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
        "dia_semana": DIAS[datetime.strptime(fecha, "%Y-%m-%d").weekday()],
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
        "dia_semana": DIAS[datetime.strptime(fecha, "%Y-%m-%d").weekday()],
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


def _escribir_csv(ruta: Path, filas: list[dict]) -> None:
    if not filas:
        ruta.write_text("", encoding="utf-8")
        return
    with ruta.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        escritor.writeheader()
        escritor.writerows(filas)


def _markdown(usuario: str, sesiones, por_sesion: dict) -> str:
    lineas = [
        f"# Histórico de entrenamientos — {usuario}",
        "",
        f"Exportado el {datetime.now():%Y-%m-%d %H:%M}. "
        f"{len(sesiones)} sesiones registradas.",
        "",
    ]
    for s in sesiones:
        items = por_sesion[s["id"]]
        fecha = s["fecha"][:10]
        dia = DIAS[datetime.strptime(fecha, "%Y-%m-%d").weekday()]
        lineas += [
            f"## {fecha} ({dia}) · Familia {s['familia']} · {s['estado']}",
            "",
            f"- Recuperación: {s['recuperacion'] or '—'} · dolor: "
            f"{s['dolor'] if s['dolor'] is not None else '—'} · "
            f"BJJ: {s['bjj_disponible'] or '—'}"
            + (f" ({s['tipo_bjj']})" if s["tipo_bjj"] else ""),
            f"- RPE real: {s['rpe_real'] if s['rpe_real'] is not None else '—'} · "
            f"sensación: {s['sensacion'] or '—'} · "
            f"molestias: {_lista(s['molestias']) or 'ninguna'} · "
            f"duración estimada: {s['duracion_estimada_min'] or '—'} min",
            "",
            "| Bloque | Ejercicio | Dosis prevista | Estado | Dosis real | Peso (kg) |",
            "|---|---|---|---|---|---|",
        ]
        for it in items:
            real = it["exercise_id_real"]
            nombre = it["exercise_id"] + (f" → {real}" if real else "")
            lineas.append(
                f"| {it['bloque']} | {nombre} | {it['dosis']} | {it['estado']} | "
                f"{_real(it) or '—'} | {it['carga_kg_real'] if it['carga_kg_real'] is not None else '—'} |"
            )
        lineas.append("")
    return "\n".join(lineas)


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta el historial de un usuario a CSV/Markdown.")
    parser.add_argument("--usuario", required=True, help="nombre de usuario (`username`)")
    parser.add_argument("--salida", type=Path, default=SALIDA_POR_DEFECTO, help="directorio de salida")
    args = parser.parse_args()

    conn, ruta_bd = abrir_bd()
    user_id = _usuario(conn, args.usuario)
    catalog = load_default_catalog()
    dimensiones = list(catalog.valores["dimensiones"])

    sesiones = conn.execute(SESIONES_SQL, (user_id,)).fetchall()
    items = conn.execute(ITEMS_SQL, (user_id,)).fetchall()
    if not sesiones:
        print(f"El usuario «{args.usuario}» no tiene ninguna sesión registrada en {ruta_bd}.")
        return 0

    por_sesion: dict[int, list] = {}
    for it in items:
        por_sesion.setdefault(it["session_id"], []).append(it)

    filas_sesion = [_filas_sesion(s, por_sesion.get(s["id"], []), dimensiones) for s in sesiones]
    filas_ejercicios = [
        fila for s in sesiones for fila in _filas_ejercicios(s, por_sesion.get(s["id"], []), catalog, dimensiones)
    ]

    args.salida.mkdir(parents=True, exist_ok=True)
    _escribir_csv(args.salida / "sesiones.csv", filas_sesion)
    _escribir_csv(args.salida / "ejercicios.csv", filas_ejercicios)
    (args.salida / "historico.md").write_text(
        _markdown(args.usuario, sesiones, por_sesion), encoding="utf-8"
    )

    cerradas = sum(1 for s in sesiones if s["estado"] == "cerrada")
    completados = sum(1 for f in filas_ejercicios if f["estado_item"] == "completado")
    print(f"Exportado el historial de «{args.usuario}» desde {ruta_bd}:")
    print(f"  {len(sesiones)} sesiones ({cerradas} cerradas), {len(filas_ejercicios)} ejercicios ({completados} completados)")
    print(f"  {sesiones[0]['fecha'][:10]} → {sesiones[-1]['fecha'][:10]}")
    for nombre in ("sesiones.csv", "ejercicios.csv", "historico.md"):
        print(f"  {args.salida / nombre}")
    print("\nAviso: es un export de datos de salud; no lo muevas a una ruta versionada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
