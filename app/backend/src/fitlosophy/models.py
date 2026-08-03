"""Modelos de datos del dominio (docs/11) con dataclasses.

Identificadores en inglés; valores de dominio en español, exactamente como en
los YAML y los documentos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

# Valores de dominio
RECUPERACIONES = ("verde", "amarillo", "rojo")
BJJ_DISPONIBLE = ("si", "no", "incierto")
TIPOS_BJJ = ("tecnico", "normal", "duro")
FAMILIAS = ("A", "B", "C", "D")
NIVELES_CARGA = ("baja", "media", "alta")


@dataclass
class DailyState:
    """Estado diario: cuestionario mínimo de docs/03.

    - `dolor` se declara siempre (0 = sin dolor); nunca None (docs/11).
    - `material_disponible`: conjunto de tokens del catálogo ('kettlebell',
      'goma', 'cinta', ...). None = todo el inventario del perfil. El conjunto
      vacío = modo sin material (viaje). El tatami se asume siempre.
    """

    fecha: datetime
    recuperacion: str
    dolor: int
    bjj_disponible: str
    zona_dolor: str | None = None
    tipo_bjj: str | None = None
    limitacion: str | None = None
    material_disponible: frozenset[str] | None = None
    tiempo_disponible: int | None = None  # minutos
    preferencia: str | None = None  # fuerza|potencia|acondicionamiento|tecnica|recuperacion
    circunstancias: str | None = None


@dataclass
class BjjRecord:
    """Registro de BJJ (entidad de docs/11). Su carga es estimada (docs/12)."""

    fecha: datetime
    clasificacion: str  # tecnico | normal | duro
    duracion_minutos: int = 75
    fatiga_agarre: bool = False
    estimado: bool = False  # True si se infiere ante datos incompletos (docs/12)


@dataclass
class PerformedExercise:
    """Ejercicio realizado dentro de una sesión física registrada.

    `puntos`: puntos por dimensión realmente computados en la sesión (p. ej.
    los puntos de la sesión propuesta que se ejecutó). Si es None, se calcula
    con el coste base completo de la biblioteca (sesión registrada a mano,
    docs/12). `cuenta_estimulo=False` para ejercicios de B0/B4 o dosis de
    recuperación: no cuentan como estímulo del patrón a efectos de P1.
    """

    exercise_id: str
    puntos: dict[str, float] | None = None
    volumen_sobre_rango: bool = False
    al_fallo: bool = False
    rpe_real: int | None = None
    fatiga_previa_alta: bool = False
    cuenta_estimulo: bool = True


@dataclass
class PerformedSession:
    """Sesión física realizada (registrada)."""

    fecha: datetime
    ejercicios: list[PerformedExercise]
    familia: str | None = None
    rpe_real: int | None = None


Event = BjjRecord | PerformedSession


@dataclass
class LoadVector:
    """Carga activa por dimensión (variable derivada, docs/12)."""

    puntos: dict[str, float]
    niveles: dict[str, str]  # baja | media | alta
    total: str  # nivel de la dimensión derivada `total`
    restringidas: list[str] = field(default_factory=list)  # presupuesto crítico (I1)
    conservadoras: list[str] = field(default_factory=list)  # doble sesión previa (regla 2)
    origenes: dict[str, list[str]] = field(default_factory=dict)  # dim -> qué sesiones la generaron
    incertidumbres: list[str] = field(default_factory=list)  # datos estimados/desconocidos


@dataclass
class Proposal:
    """Salida del motor de decisión (docs/03, paso 8)."""

    fecha: datetime
    familia: str  # A | B | C | D
    reducida: bool = False
    descanso_opcion: bool = False  # D1/D2: recuperación activa o descanso
    techo: str = "potente"  # potente | media | compatible | recuperacion
    bjj_efectivo: str | None = None  # tipo de BJJ asumido (C5: incierto -> normal)
    presupuestos: dict[str, float] = field(default_factory=dict)
    patrones_prioritarios: list[str] = field(default_factory=list)
    patrones_restringidos: dict[str, str] = field(default_factory=dict)  # patrón -> motivo con código
    patrones_dosificados: list[str] = field(default_factory=list)  # C2
    d3_activa: bool = False
    d4_activa: bool = False
    d5_activa: bool = False
    reglas_aplicadas: list[str] = field(default_factory=list)
    incertidumbres: list[str] = field(default_factory=list)
    carga: LoadVector | None = None
    explicacion: str = ""


@dataclass
class SessionItem:
    """Ejercicio dosificado dentro de un bloque de la sesión propuesta."""

    exercise_id: str
    bloque: str  # B0 | B1 | B2 | B3 | B4 | continuo
    dosis: str  # texto legible: "3×10", "2×30 s", "30 min"
    puntos: dict[str, float] = field(default_factory=dict)  # {} en B0/B4 (no computan, regla 8)
    justificacion: str = ""


@dataclass
class SessionProposal:
    """Sesión propuesta completa (entidad de docs/11)."""

    fecha: datetime
    familia: str
    items: list[SessionItem]
    puntos_sesion: dict[str, float] = field(default_factory=dict)
    duracion_estimada_min: int = 0
    valida: bool = True
    violaciones: list[str] = field(default_factory=list)
    notas: list[str] = field(default_factory=list)  # recortes, patrones pendientes...

    def items_bloque(self, bloque: str) -> list[SessionItem]:
        return [i for i in self.items if i.bloque == bloque]
