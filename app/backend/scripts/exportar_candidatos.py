"""Regenera `data/candidatos.yaml` desde la tabla `candidates` (docs/15).

El fichero sigue siendo un registro no ejecutable: guarda la trazabilidad de
los candidatos importados (dataset, estado, decisión, fecha) sin que el motor
pueda leerlo. Las entradas **importadas** se regeneran desde la BD; las
entradas del **flujo manual** (sin `dataset_id`: no provienen de un dataset) se
conservan tal cual, porque no viven en ninguna tabla y borrarlas sería perder
la investigación.

Uso:
    cd app/backend
    ./.venv/bin/python scripts/exportar_candidatos.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fitlosophy_api.candidatos import DATA_DIR  # noqa: E402
from fitlosophy_api.db import cargar_json  # noqa: E402

CABECERA = """\
version: 1

# Este fichero no es parte del catálogo ejecutable. El motor y la aplicación
# solo leen `ejercicios.yaml`; una entrada aquí nunca puede proponerse sola.
# Las entradas con `dataset_id` provienen de la importación masiva (docs/15) y
# las regenera app/backend/scripts/exportar_candidatos.py desde la tabla
# `candidates`: no se editan a mano. Las entradas sin `dataset_id` son del
# flujo manual y este script las conserva tal cual.
estados:
  - pendiente_de_evidencia
  - candidato
  - experimental
  - descartado
"""

FUENTE = "exercises-dataset (Gym visual) — https://gymvisual.com/"


def _entradas_manuales(ruta: Path) -> list[dict]:
    """Entradas del flujo manual en el YAML actual: las que no tienen
    `dataset_id`, es decir, las que no salieron de una importación."""
    if not ruta.is_file():
        return []
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
    return [c for c in datos.get("candidatos") or [] if not c.get("dataset_id")]


def exportar(conn, ruta: Path | None = None) -> dict:
    """Escribe `data/candidatos.yaml`: entradas manuales conservadas + filas de
    la BD. Devuelve contadores."""
    ruta = ruta or DATA_DIR / "candidatos.yaml"
    manuales = _entradas_manuales(ruta)
    filas = conn.execute(
        "SELECT * FROM candidates ORDER BY estado, id"
    ).fetchall()
    importados = []
    for f in filas:
        importados.append(
            {
                "id_provisional": cargar_json(f["etiquetas_inferidas"], {}).get("id"),
                "dataset_id": f["dataset_id"],
                "nombre_en": f["nombre_en"],
                "nombre_es": f["nombre_es"],
                "fuente": FUENTE,
                "equipment": f["equipment"],
                "grupo_muscular": f["muscle_group"],
                "material_fitlosophy": cargar_json(f["material_fitlosophy"], []),
                "posible_equivalente": f["posible_equivalente"],
                "estado": f["estado"],
                "motivo_descarte": f["motivo_descarte"],
                "fecha_importacion": f["created_at"],
                "fecha_decision": f["revisado_at"],
                "etiquetas": cargar_json(f["etiquetas_finales"], None)
                or cargar_json(f["etiquetas_inferidas"], {}),
            }
        )
    with ruta.open("w", encoding="utf-8") as fh:
        fh.write(CABECERA)
        yaml.safe_dump(
            {"candidatos": manuales + importados}, fh, allow_unicode=True, sort_keys=False, width=100
        )
    return {"manuales": len(manuales), "importados": len(importados)}


def main() -> int:
    from _comun import abrir_bd

    conn, _ = abrir_bd()
    try:
        res = exportar(conn)
    finally:
        conn.close()
    print(
        f"data/candidatos.yaml regenerado: {res['importados']} importados desde la BD "
        f"+ {res['manuales']} entradas manuales conservadas."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
