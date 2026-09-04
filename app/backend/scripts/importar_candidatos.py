"""Importa un dataset de ejercicios como candidatos revisables (docs/15).

Lee el JSON del dataset, descarta lo no ejecutable con el material de
`data/perfil.yaml`, infiere un borrador conservador de etiquetas y vuelca todo
en la tabla `candidates`. Los GIFs se copian a `media/candidatos/`.

Idempotente: la clave es `dataset_id`; reejecutar no duplica ni toca lo ya
revisado.

Uso:
    cd app/backend
    ./.venv/bin/python scripts/importar_candidatos.py ../../temp/exercises-dataset/data/exercises.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fitlosophy.catalog import Catalog, load_default_perfil  # noqa: E402
from fitlosophy_api.candidatos import (  # noqa: E402
    DATA_DIR,
    MEDIA_CANDIDATOS,
    equivalente_probable,
    inferir_etiquetas,
    material_para_equipment,
)
from fitlosophy_api.db import volcar_json  # noqa: E402

FUENTE = "exercises-dataset (Gym visual)"


def importar(
    conn: sqlite3.Connection,
    ruta_json: Path,
    videos_dir: Path | None = None,
    media_dir: Path | None = None,
    catalogo: Catalog | None = None,
) -> dict:
    """Vuelca el dataset en `candidates`. Devuelve contadores del proceso."""
    perfil = load_default_perfil()
    if catalogo is None:
        catalogo = Catalog.load(DATA_DIR / "ejercicios.yaml")
    videos_dir = videos_dir or ruta_json.resolve().parent.parent / "videos"
    media_dir = media_dir or MEDIA_CANDIDATOS

    registros = json.loads(ruta_json.read_text(encoding="utf-8"))
    ahora = datetime.now().isoformat(timespec="seconds")
    resultado = {"importados": 0, "ya_presentes": 0, "descartados_material": 0, "por_equipment": {}}

    for reg in registros:
        equipment = reg.get("equipment") or ""
        if conn.execute("SELECT 1 FROM candidates WHERE dataset_id = ?", (reg["id"],)).fetchone():
            resultado["ya_presentes"] += 1
            continue

        material = material_para_equipment(equipment, reg.get("name") or "", set(perfil.material))
        if material is None:
            resultado["descartados_material"] += 1
            continue

        gif = None
        media_id = reg.get("media_id")
        if media_id:
            origen = videos_dir / f"{reg['id']}-{media_id}.gif"
            if origen.is_file():
                media_dir.mkdir(parents=True, exist_ok=True)
                destino = media_dir / origen.name
                if not destino.exists():
                    shutil.copy2(origen, destino)
                gif = origen.name

        etiquetas = inferir_etiquetas(reg, material)
        conn.execute(
            """INSERT INTO candidates (
                dataset_id, nombre_en, nombre_es, instrucciones_es, equipment, body_part,
                muscle_group, secondary_muscles, gif, material_fitlosophy,
                etiquetas_inferidas, posible_equivalente, estado, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pendiente_revision', ?)""",
            (
                reg["id"],
                reg.get("name") or "",
                reg.get("name") or "",  # la traducción es tarea de la revisión
                (reg.get("instructions") or {}).get("es") or "",
                equipment,
                reg.get("body_part") or "",
                reg.get("muscle_group") or "",
                volcar_json(reg.get("secondary_muscles") or []),
                gif,
                volcar_json(material),
                volcar_json(etiquetas),
                equivalente_probable(reg.get("name") or "", catalogo),
                ahora,
            ),
        )
        resultado["importados"] += 1
        resultado["por_equipment"][equipment] = resultado["por_equipment"].get(equipment, 0) + 1

    conn.commit()
    return resultado


def main() -> int:
    ap = argparse.ArgumentParser(description="Importa un dataset de ejercicios como candidatos (docs/15).")
    ap.add_argument("json", help="ruta al exercises.json del dataset")
    ap.add_argument("--videos", help="directorio con los GIFs (por defecto: <dataset>/videos)")
    args = ap.parse_args()

    from _comun import abrir_bd

    conn, _ = abrir_bd()
    try:
        resultado = importar(
            conn,
            Path(args.json),
            videos_dir=Path(args.videos) if args.videos else None,
        )
    finally:
        conn.close()

    print(f"Importados: {resultado['importados']}")
    for equipment, n in sorted(resultado["por_equipment"].items(), key=lambda kv: -kv[1]):
        print(f"  · {equipment}: {n}")
    print(f"Ya presentes (idempotencia): {resultado['ya_presentes']}")
    print(f"Descartados por material no disponible: {resultado['descartados_material']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
