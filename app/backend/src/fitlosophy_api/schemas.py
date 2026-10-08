"""Esquemas de entrada de la API (pydantic, incluido con FastAPI).

Valores de dominio en español, exactamente como en los documentos.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Recuperacion = Literal["verde", "amarillo", "rojo"]
BjjDisponible = Literal["si", "no", "incierto"]
TipoBjj = Literal["tecnico", "normal", "duro"]
EstadoItem = Literal["completado", "modificado", "sustituido", "no_realizado"]
Sensacion = Literal["como_previsto", "mas_duro", "mas_suave"]


class EstadoDiarioIn(BaseModel):
    """Cuestionario diario mínimo de docs/03 (pantalla 1 de docs/14)."""

    recuperacion: Recuperacion
    dolor: int = Field(ge=0, le=10)
    bjj_disponible: BjjDisponible
    zona_dolor: str | None = None
    tipo_bjj: TipoBjj | None = None
    limitacion: str | None = None
    sueno: str | None = None
    tiempo_disponible: int | None = Field(default=None, gt=0)
    preferencia: str | None = None
    circunstancias: str | None = None
    material_disponible: list[str] | None = None  # None = todo el garaje; [] = sin material

    @model_validator(mode="after")
    def zona_si_dolor(self):
        if self.dolor > 0 and not self.zona_dolor:
            raise ValueError("Si el dolor es mayor que 0 hay que indicar la zona")
        return self


class SustituirIn(BaseModel):
    item_indice: int = Field(ge=0)
    exercise_id: str


class SesionIn(BaseModel):
    proposal_id: int


class ItemPatchIn(BaseModel):
    estado: EstadoItem
    exercise_id_real: str | None = None  # obligatorio si estado = sustituido
    series_real: int | None = Field(default=None, gt=0)
    repeticiones_real: int | None = Field(default=None, gt=0)
    segundos_real: float | None = Field(default=None, gt=0)
    minutos_real: float | None = Field(default=None, gt=0)
    carga_kg_real: float | None = Field(default=None, ge=0)
    motivo: str | None = None

    @model_validator(mode="after")
    def campos_segun_estado(self):
        if self.estado == "sustituido" and not self.exercise_id_real:
            raise ValueError("Un ítem sustituido exige exercise_id_real")
        if self.estado == "modificado" and not any(
            v is not None
            for v in (self.series_real, self.repeticiones_real, self.segundos_real, self.minutos_real, self.carga_kg_real)
        ):
            raise ValueError("Un ítem modificado exige al menos un valor real")
        return self


class FinalizarIn(BaseModel):
    rpe_real: int = Field(ge=1, le=10)


class MolestiaIn(BaseModel):
    zona: str
    intensidad: int = Field(ge=0, le=10)


class CierreIn(BaseModel):
    sensacion: Sensacion
    molestias: list[MolestiaIn] = []


class CierrePut(BaseModel):
    sensacion: Sensacion | None = None
    molestias: list[MolestiaIn] | None = None


class BjjIn(BaseModel):
    """Registro manual de BJJ (docs/11): clasificación y duración obligatorios."""

    clasificacion: TipoBjj
    duracion_minutos: int = Field(gt=0)
    fecha: datetime | None = None  # por defecto, ahora
    fatiga_agarre: bool = False
    intensidad_percibida: int | None = Field(default=None, ge=1, le=10)
    notas: str | None = None


class BjjPut(BaseModel):
    clasificacion: TipoBjj | None = None
    duracion_minutos: int | None = Field(default=None, gt=0)
    fecha: datetime | None = None
    fatiga_agarre: bool | None = None
    intensidad_percibida: int | None = Field(default=None, ge=1, le=10)
    notas: str | None = None


class SesionPut(BaseModel):
    rpe_real: int | None = Field(default=None, ge=1, le=10)
    fecha: datetime | None = None


class PerfilPut(BaseModel):
    data: dict


ZonaMolestia = Literal[
    "lumbar", "cervical", "hombros", "brazos_manos", "cadera", "rodillas", "piernas_pies", "otras"
]


class BienestarIn(BaseModel):
    """Registro matutino de bienestar (docs/morning_state).

    Todo opcional: se guardan registros parciales. Uno por usuario y fecha;
    es informativo y no modifica la planificación.
    """

    calidad_sueno: int | None = Field(default=None, ge=1, le=5)
    recuperacion_fisica: int | None = Field(default=None, ge=1, le=5)
    molestias_fisicas: int | None = Field(default=None, ge=0, le=10)
    zonas_molestias: list[ZonaMolestia] = []
    energia_fisica: int | None = Field(default=None, ge=1, le=5)
    claridad_mental: int | None = Field(default=None, ge=1, le=5)
    estres_previsto: int | None = Field(default=None, ge=1, le=5)
    observaciones: str | None = None

    @model_validator(mode="after")
    def zonas_solo_con_molestias(self):
        # La localización solo tiene sentido si hay molestias declaradas.
        if not self.molestias_fisicas:
            self.zonas_molestias = []
        return self


class ActividadIn(BaseModel):
    """Actividad externa (docs/morning_state/especificacion_actividad_externa.md).

    `combates` vacío queda no informado (NULL), que no es lo mismo que 0.
    BJJ y grappling mantienen además un `bjj_records` enlazado que alimenta el
    motor (excepción documentada en la especificación, §1).
    """

    fecha: date
    tipo: Literal["bjj", "grappling", "otra"]
    duracion_minutos: int = Field(gt=0)
    rpe: int = Field(ge=1, le=10)
    nombre: str | None = None
    combates: int | None = Field(default=None, ge=0)
    observaciones: str | None = None
    # Solo para bjj/grappling: se propaga al registro que alimenta el motor
    # (bjj_records), que es la única parte del alta que no es informativa.
    fatiga_agarre: bool = False

    @model_validator(mode="after")
    def nombre_si_otra(self):
        if self.tipo == "otra" and not (self.nombre and self.nombre.strip()):
            raise ValueError("Con tipo «otra» hay que indicar el nombre de la actividad")
        return self

    @model_validator(mode="after")
    def nada_de_futuro(self):
        # Registra lo ya hecho; planificar actividades futuras está fuera de alcance.
        if self.fecha > date.today():
            raise ValueError("No se puede registrar una actividad en una fecha futura")
        return self


class CandidatoPutIn(BaseModel):
    """Etiquetas confirmadas/corregidas por el revisor en la UI (docs/15)."""

    etiquetas_finales: dict


class DescartarIn(BaseModel):
    motivo: str | None = None
