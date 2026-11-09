"""Repara las descripciones de los ejercicios aceptados desde el dataset.

La importación de docs/15 generaba la descripción con las **dos primeras
frases** de las instrucciones del dataset y la recortaba a 300 caracteres. Las
instrucciones traen 4-7 frases (preparación, ejecución, retorno), así que los
ejercicios aceptados quedaron con explicaciones a medias: describían la
posición inicial y omitían el movimiento.

Este script recalcula la descripción con la regla actual (`_descripcion`:
frases completas hasta ~500 caracteres), actualiza `data/ejercicios.yaml`
**por bloque de texto** —sin reordenar ni reformatear el resto del fichero— y
deja el mismo texto en el borrador revisado de la tabla `candidates`.

Uso:
    cd app/backend
    ./.venv/bin/python scripts/reparar_descripciones.py            # simulación
    ./.venv/bin/python scripts/reparar_descripciones.py --aplicar  # escribe
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fitlosophy_api.candidatos import DATA_DIR, _descripcion, slug_id  # noqa: E402
from fitlosophy_api.db import cargar_json  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comun import abrir_bd  # noqa: E402

RUTA_YAML = DATA_DIR / "ejercicios.yaml"
ANCHO = 92


def _envolver(texto: str) -> list[str]:
    return textwrap.wrap(texto, width=ANCHO, break_long_words=False, break_on_hyphens=False)


def _reemplazar_descripcion(texto: str, exercise_id: str, nueva: str) -> str:
    """Sustituye el bloque `descripcion` de un ejercicio conservando el resto.

    El valor pasa a escalar plegado (`>-`), que no reinterpreta `:` ni `#` y
    mantiene una sola cadena al cargar el YAML.
    """
    lineas = texto.splitlines(keepends=True)
    inicio = next(
        (i for i, linea in enumerate(lineas) if linea.strip() == f"- id: {exercise_id}"), None
    )
    if inicio is None:
        raise KeyError(f"ejercicio no encontrado: {exercise_id}")
    fin = len(lineas)
    for j in range(inicio + 1, len(lineas)):
        if lineas[j].lstrip().startswith("- id: "):
            fin = j
            break
    for k in range(inicio + 1, fin):
        if lineas[k].startswith("    descripcion:"):
            fin_desc = k + 1
            while fin_desc < fin and lineas[fin_desc].startswith("      "):
                fin_desc += 1
            envuelto = [f"    descripcion: >-\n"] + [f"      {linea}\n" for linea in _envolver(nueva)]
            return "".join(lineas[:k] + envuelto + lineas[fin_desc:])
    raise KeyError(f"descripcion no encontrada: {exercise_id}")


def _impacto(row) -> str:
    etiquetas = cargar_json(row["etiquetas_finales"], None) or cargar_json(
        row["etiquetas_inferidas"], {}
    )
    return (etiquetas or {}).get("impacto_lumbar") or "verde"


def _descripcion_antigua(instrucciones: str, impacto: str) -> str:
    """Regla anterior (dos frases, 300 caracteres) para detectar ediciones humanas.

    Si la descripción del catálogo no coincide con lo que producía la regla
    antigua, una persona la reescribió en la revisión y no se toca.
    """
    import re

    frases = [
        f.strip() for f in re.split(r"(?<=[.!?])\s+", instrucciones.replace("\n", " ")) if f.strip()
    ]
    desc = " ".join(frases[:2])[:300].strip()
    if impacto == "rojo":
        desc = (desc + " Detén el ejercicio si aparece molestia lumbar.").strip()
    return desc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aplicar", action="store_true", help="escribe los cambios (sin él, simula)")
    args = parser.parse_args()

    texto = RUTA_YAML.read_text(encoding="utf-8")
    datos = yaml.safe_load(texto)
    catalogo = {e["id"]: e for e in datos["exercises"]}

    conn, _ = abrir_bd()
    filas = conn.execute(
        "SELECT id, nombre_en, instrucciones_es, etiquetas_finales, etiquetas_inferidas "
        "FROM candidates WHERE estado = 'aceptado' ORDER BY nombre_en"
    ).fetchall()

    cambios: list[tuple[int, str, str, str]] = []  # (candidate_id, exercise_id, antes, nueva)
    avisos: list[str] = []
    for row in filas:
        exercise_id = slug_id(row["nombre_en"])
        if exercise_id not in catalogo:
            avisos.append(f"{row['nombre_en']}: id {exercise_id} no está en el catálogo; se omite")
            continue
        nueva = _descripcion({"instructions": {"es": row["instrucciones_es"]}}, _impacto(row))
        antes = catalogo[exercise_id]["descripcion"]
        if antes == nueva:
            continue
        if antes != _descripcion_antigua(row["instrucciones_es"], _impacto(row)):
            avisos.append(f"{exercise_id}: descripción editada a mano en la revisión; se conserva")
            continue
        cambios.append((row["id"], exercise_id, antes, nueva))
        texto = _reemplazar_descripcion(texto, exercise_id, nueva)

    # Verificación antes de escribir: el YAML sigue siendo válido y cada
    # descripción sustituida coincide exactamente con la regenerada.
    comprobado = {e["id"]: e for e in yaml.safe_load(texto)["exercises"]}
    for _, exercise_id, _, nueva in cambios:
        if comprobado[exercise_id]["descripcion"] != nueva:
            print(f"ERROR: la sustitución de {exercise_id} no se leyó igual; no se escribe nada")
            return 1

    for _, exercise_id, antes, nueva in cambios:
        print(f"- {exercise_id}")
        print(f"  antes: {antes}")
        print(f"  nueva: {nueva}")
    print(f"\n{len(cambios)} descripciones a reparar, {len(avisos)} avisos.")
    for aviso in avisos:
        print(f"AVISO: {aviso}")

    if not args.aplicar:
        print("\nSimulación: no se ha escrito nada. Usa --aplicar para aplicar.")
        return 0

    RUTA_YAML.write_text(texto, encoding="utf-8")
    for candidate_id, _, _, nueva in cambios:
        fila = conn.execute("SELECT etiquetas_finales FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        etiquetas = cargar_json(fila["etiquetas_finales"], None)
        if not etiquetas:
            continue  # sin borrador revisado propio: solo se toca el catálogo
        etiquetas["descripcion"] = nueva
        conn.execute(
            "UPDATE candidates SET etiquetas_finales = ? WHERE id = ?",
            (json.dumps(etiquetas, ensure_ascii=False), candidate_id),
        )
    conn.commit()
    print(f"\nAplicado: {len(cambios)} descripciones actualizadas en el catálogo y en la BD.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
