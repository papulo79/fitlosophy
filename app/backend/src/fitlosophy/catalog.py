"""Carga del catálogo de ejercicios (`data/ejercicios.yaml`) y del perfil (`data/perfil.yaml`).

El catálogo es la fuente de verdad de la biblioteca (docs/05). Los valores
categóricos se conservan exactamente como en el YAML (español).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

# Raíz del repositorio: app/backend/src/fitlosophy/catalog.py -> 4 niveles hasta app/, 5 hasta la raíz.
REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = REPO_ROOT / "data"

# Dimensiones de carga definitivas (docs/12). `total` no se asigna: se deriva.
DIMENSIONES = [
    "lumbar",
    "bisagra",
    "rodilla_piernas",
    "empuje",
    "tiron",
    "agarre",
    "core",
    "cardio",
    "impacto_articular",
]

# Puntos por nivel de coste (docs/12, provisional).
PUNTOS_COSTE = {"bajo": 1.0, "medio": 2.0, "alto": 3.0}

# Patrón de movimiento -> dimensiones que alimenta (docs/05).
# `hombro` no es dimensión en docs/12; el trabajo de hombro computa en `empuje`.
PATRON_DIMENSIONES = {
    "empuje_horizontal": ["empuje"],
    "empuje_vertical": ["empuje"],
    "tiron_horizontal": ["tiron", "agarre"],
    "tiron_vertical": ["tiron", "agarre"],
    "dominante_rodilla": ["rodilla_piernas"],
    "dominante_cadera": ["bisagra", "lumbar"],
    "core_antiextension": ["core", "lumbar"],
    "core_antirotacion": ["core"],
    "core_lateral": ["core"],
    "core_flexion_cadera": ["core", "agarre"],
    "core_rotacion": ["core"],
    "acondicionamiento": ["cardio", "impacto_articular"],
    "agilidad": ["cardio", "impacto_articular", "rodilla_piernas"],
    "movilidad_cargada": ["lumbar", "empuje"],
    "recuperacion": [],
}

# Material del catálogo -> clave del inventario de perfil.yaml (por concepto, AGENTS.md).
MATERIAL_A_PERFIL = {
    "trx": "trx",
    "tatami": "tatami",
    "barra_dominadas": "barra_dominadas",
    "kettlebell": "kettlebells_kg",
    "comba": "comba",
    "caja": "caja",
    "goma": "gomas",
    "conos": "conos",
    "escalera_agilidad": "escalera_agilidad",
    "cinta": "cinta_velocidad_max_kmh",
}


@dataclass(frozen=True)
class Exercise:
    """Ejercicio del catálogo (entidad Ejercicio de docs/11)."""

    id: str
    nombre: str
    patron: str
    secundarios: tuple[str, ...] = ()
    material: tuple[str, ...] = ()
    sin_material: bool = False
    nivel: str = "base"
    lateralidad: str = "bilateral"
    explosivo: bool = False
    isometrico: bool = False
    coste_dimensiones: dict[str, str] = field(default_factory=dict)
    impacto_lumbar: str = "verde"
    compatibilidad_bjj: str = "si"
    objetivos: tuple[str, ...] = ()
    progresiones: tuple[str, ...] = ()
    regresiones: tuple[str, ...] = ()
    sustitutos: tuple[str, ...] = ()
    prescripcion: dict = field(default_factory=dict)
    opcional: bool = False

    def coste(self, dimension: str) -> str | None:
        return self.coste_dimensiones.get(dimension)

    def disponible_con(self, material_disponible: set[str] | frozenset[str]) -> bool:
        """Filtro de material (docs/06, regla 9).

        `sin_material: true` entra siempre; el tatami cuenta como suelo
        (siempre disponible).
        """
        if self.sin_material:
            return True
        return all(m == "tatami" or m in material_disponible for m in self.material)

    def dimensiones_alimentadas(self) -> set[str]:
        """Dimensiones que alimenta el patrón principal (docs/05)."""
        return set(PATRON_DIMENSIONES.get(self.patron, []))

    def dimensiones_secundarias(self) -> set[str]:
        dims: set[str] = set()
        for sec in self.secundarios:
            dims.update(PATRON_DIMENSIONES.get(sec, []))
        return dims


@dataclass(frozen=True)
class Perfil:
    """Datos del atleta (data/perfil.yaml). Solo lo que el motor necesita."""

    material: frozenset[str]
    bjj_sesiones_semana_min: int = 3
    raw: dict = field(default_factory=dict)


class Catalog:
    """Catálogo de ejercicios indexado por id."""

    def __init__(self, ejercicios: list[Exercise], valores: dict | None = None):
        self._por_id = {e.id: e for e in ejercicios}
        self.ejercicios = list(ejercicios)
        self.valores = valores or {}

    @classmethod
    def load(cls, path: str | Path) -> "Catalog":
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        ejercicios = []
        for e in data["exercises"]:
            ejercicios.append(
                Exercise(
                    id=e["id"],
                    nombre=e["nombre"],
                    patron=e["patron"],
                    secundarios=tuple(e.get("secundarios", ())),
                    material=tuple(e.get("material", ())),
                    sin_material=bool(e.get("sin_material", False)),
                    nivel=e.get("nivel", "base"),
                    lateralidad=e.get("lateralidad", "bilateral"),
                    explosivo=bool(e.get("explosivo", False)),
                    isometrico=bool(e.get("isometrico", False)),
                    coste_dimensiones=dict(e.get("coste_dimensiones", {})),
                    impacto_lumbar=e.get("impacto_lumbar", "verde"),
                    compatibilidad_bjj=e.get("compatibilidad_bjj", "si"),
                    objetivos=tuple(e.get("objetivos", ())),
                    progresiones=tuple(e.get("progresiones", ())),
                    regresiones=tuple(e.get("regresiones", ())),
                    sustitutos=tuple(e.get("sustitutos", ())),
                    prescripcion=dict(e.get("prescripcion", {})),
                    opcional=bool(e.get("opcional", False)),
                )
            )
        return cls(ejercicios, valores=data.get("valores", {}))

    def __getitem__(self, ejercicio_id: str) -> Exercise:
        return self._por_id[ejercicio_id]

    def get(self, ejercicio_id: str) -> Exercise | None:
        return self._por_id.get(ejercicio_id)

    def __iter__(self):
        return iter(self.ejercicios)

    def __len__(self) -> int:
        return len(self.ejercicios)

    @property
    def patrones(self) -> list[str]:
        """Taxonomía cerrada de patrones, en el orden del YAML."""
        return list(self.valores.get("patron", PATRON_DIMENSIONES.keys()))


def load_default_catalog() -> Catalog:
    return Catalog.load(DATA_DIR / "ejercicios.yaml")


def load_default_perfil() -> Perfil:
    data = yaml.safe_load((DATA_DIR / "perfil.yaml").read_text(encoding="utf-8"))
    material = set()
    for token, clave in MATERIAL_A_PERFIL.items():
        valor = data.get("material", {}).get(clave)
        if valor:  # true o lista no vacía o número
            material.add(token)
    bjj = data.get("bjj", {})
    return Perfil(
        material=frozenset(material),
        bjj_sesiones_semana_min=int(bjj.get("sesiones_semana", {}).get("min", 3)),
        raw=data,
    )
