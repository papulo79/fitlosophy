"""Fitlosophy: motor de decisión diario y generador de sesiones.

Implementación fiel a la especificación del modelo de dominio:
- docs/12: modelo de carga e inferencia (`load.py`)
- docs/03: motor de decisión (`engine.py`)
- docs/06: generador de sesiones (`generator.py`)
"""

from .catalog import Catalog, Exercise, Perfil, load_default_catalog, load_default_perfil
from .models import (
    BjjRecord,
    DailyState,
    LoadVector,
    PerformedExercise,
    PerformedSession,
    Proposal,
    SessionItem,
    SessionProposal,
)
from .load import compute_load
from .engine import decide
from .generator import check_substitution, generate, validate_session

__all__ = [
    "BjjRecord",
    "Catalog",
    "DailyState",
    "Exercise",
    "LoadVector",
    "Perfil",
    "PerformedExercise",
    "PerformedSession",
    "Proposal",
    "SessionItem",
    "SessionProposal",
    "check_substitution",
    "compute_load",
    "decide",
    "generate",
    "load_default_catalog",
    "load_default_perfil",
    "validate_session",
]
