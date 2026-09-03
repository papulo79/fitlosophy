"""Valida un ejercicio propuesto antes de meterlo en `data/ejercicios.yaml`.

Pensado para lo que devuelve un agente externo a partir de una transcripción o
un artículo (ver `docs/roles/prompt-ejercicio-nuevo.md`). Comprueba de forma
determinista **todo lo que es comprobable** —dominios cerrados, inventario de
material, referencias cruzadas, unicidad, coherencia de la prescripción— para
que el criterio humano se reserve a lo único que lo necesita: si el ejercicio
aporta cobertura nueva, si su impacto lumbar es correcto para este atleta y si
sus costes por dimensión son plausibles.

La lógica vive en `fitlosophy_api.validacion` para que el endpoint de
aceptación de candidatos use exactamente la misma puerta (docs/15).

Uso:
    cd app/backend
    ./.venv/bin/python scripts/validar_ejercicio.py propuesta.yaml

Devuelve 0 si es insertable y 1 si hay errores. Los avisos no bloquean.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fitlosophy.catalog import load_default_catalog, load_default_perfil  # noqa: E402
from fitlosophy_api.validacion import cobertura, validar  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Valida un ejercicio propuesto para el catálogo.")
    ap.add_argument("fichero", help="YAML con el ejercicio (lista de uno o mapa suelto)")
    ap.add_argument(
        "--confirmo-verde",
        action="store_true",
        help="permite impacto_lumbar: verde (revisado por una persona)",
    )
    args = ap.parse_args()

    datos = yaml.safe_load(Path(args.fichero).read_text(encoding="utf-8"))
    if isinstance(datos, dict) and "exercises" in datos:
        propuestas = datos["exercises"]
    elif isinstance(datos, dict):
        propuestas = [datos]
    else:
        propuestas = datos or []

    catalogo = load_default_catalog()
    perfil = load_default_perfil()
    fallos = 0

    for propuesta in propuestas:
        nombre = propuesta.get("nombre") or propuesta.get("id") or "(sin nombre)"
        print(f"\n=== {nombre} ===")
        inf = validar(propuesta, catalogo, perfil, args.confirmo_verde)

        for e in inf.errores:
            print(f"  ERROR   {e}")
        for a in inf.avisos:
            print(f"  AVISO   {a}")

        if inf.errores:
            fallos += 1
            print(f"\n  → No insertable: {len(inf.errores)} error(es).")
            continue

        print("  Sin errores de forma.")
        print()
        for linea in cobertura(propuesta, catalogo):
            print(f"  {linea}")
        print(
            "\n  Queda por decidir con criterio: si aporta cobertura nueva, si el impacto\n"
            "  lumbar es correcto para este atleta y si los costes por dimensión son\n"
            "  plausibles. Después, pégalo en data/ejercicios.yaml y ejecuta pytest."
        )

    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())
