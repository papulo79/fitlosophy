"""Regenera `data/candidatos.yaml` desde la tabla `candidates` (docs/15).

El fichero sigue siendo un registro no ejecutable: guarda la trazabilidad de
los candidatos importados (dataset, estado, decisión, fecha) sin que el motor
pueda leerlo. Se regenera entero; no se edita a mano para los importados.

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
# Regenerado por app/backend/scripts/exportar_candidatos.py desde la tabla
# `candidates`: no editar a mano las entradas importadas.
estados:
  - pendiente_de_evidencia
  - candidato
  - experimental
  - descartado
"""

FUENTE = "exercises-dataset (Gym visual) — https://gymvisual.com/"


def exportar(conn, ruta: Path | None = None) -> int:
    """Escribe `data/candidatos.yaml` desde la BD. Devuelve nº de entradas."""
    ruta = ruta or DATA_DIR / "candidatos.yaml"
    filas = conn.execute(
        "SELECT * FROM candidates ORDER BY estado, id"
    ).fetchall()
    candidatos = []
    for f in filas:
        candidatos.append(
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
            {"candidatos": candidatos}, fh, allow_unicode=True, sort_keys=False, width=100
        )
    return len(candidatos)


def main() -> int:
    from _comun import abrir_bd

    conn, _ = abrir_bd()
    try:
        n = exportar(conn)
    finally:
        conn.close()
    print(f"data/candidatos.yaml regenerado con {n} candidato(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
