"""Importación masiva de candidatos (docs/15, «Importación masiva»).

Lógica pura y testable que usan `scripts/importar_candidatos.py` y los
endpoints de revisión de `routes.py`:

- `material_para_equipment`: qué ejercicios del dataset son ejecutables con el
  inventario de `data/perfil.yaml` (los demás ni se importan).
- `inferir_etiquetas`: borrador conservador de la catalogación fitlosophy que
  el revisor confirma o corrige en la interfaz.
- `slug_id`, `equivalente_probable`: identificador y deduplicado heurístico.
- `construir_entrada`: la entrada definitiva de `ejercicios.yaml`.
- `render_entrada_yaml`: el bloque YAML que se añade al final del fichero.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = REPO_ROOT / "data"
MEDIA_CANDIDATOS = Path(__file__).resolve().parents[2] / "media" / "candidatos"

ATRIBUCION_GIF = "© Gym visual — https://gymvisual.com/"

# --- Material -----------------------------------------------------------------
#
# Equipment del dataset → tokens de material del catálogo (MATERIAL_A_PERFIL).
# `[]` = ejecutable sin material (peso corporal; el tatami cuenta como suelo).
# Lo que no aparece aquí no es ejecutable con el inventario actual y no se
# importa: cable, leverage/smith/sled machine, stability ball, bosu, medicine
# ball, roller, tire, ergómetros… y `weighted`: son fondos, dominadas o
# hiperextensiones LASTRADAS, y sin chaleco ni mancuernas en el perfil no hay
# forma de ejecutarlas como tales (importarlas como «sin material» las
# ofrecería a quien no tiene lastre).
EQUIPMENT_A_MATERIAL = {
    "body weight": [],
    "kettlebell": ["kettlebell"],
    "band": ["goma"],
    "resistance band": ["goma"],
    "rope": ["comba"],
    # Si el perfil tuviera barra, mancuernas, chaleco o bici estática, se
    # mapearían aquí; hoy el inventario no los contempla ni el catálogo tiene token.
}

# Palabras clave del nombre → material adicional que el dataset no declara.
KEYWORDS_MATERIAL = (
    (("pull up", "pull-up", "pullup", "chin up", "chin-up", "chinup", "muscle up"), "barra_dominadas"),
    (("box jump", "step up", "step-up"), "caja"),
)


def material_para_equipment(equipment: str, nombre: str, material_perfil: set[str]) -> list[str] | None:
    """Tokens de material fitlosophy, o None si no es ejecutable con el perfil.

    Un equipment mapeado a un token que el perfil no tiene también descarta el
    ejercicio (p. ej. `rope` sin comba).
    """
    base = EQUIPMENT_A_MATERIAL.get(equipment or "")
    if base is None:
        return None
    tokens = list(base)
    nombre_norm = _norm(nombre)
    for claves, token in KEYWORDS_MATERIAL:
        if any(c in nombre_norm for c in claves) and token not in tokens:
            tokens.append(token)
    if any(t not in material_perfil for t in tokens):
        return None
    return tokens


# --- Inferencia de etiquetas (borrador conservador) ----------------------------

# Palabras clave del nombre (normalizado) → patrón, en orden de prioridad:
# lo específico manda sobre la zona corporal genérica.
_REGLAS_PATRON = [
    (("pull up", "pull-up", "pullup", "chin up", "chin-up", "chinup", "muscle up", "lat pull", "shrug"), "tiron_vertical"),
    (("row", "pullover", "face pull", "rear delt"), "tiron_horizontal"),
    (("overhead press", "shoulder press", "military press", "arnold", "push press", "lateral raise", "front raise", "handstand", "pike push"), "empuje_vertical"),
    (("bench press", "chest press", "push-up", "pushup", "push up", "fly", "dip"), "empuje_horizontal"),
    (("swing", "deadlift", "hip thrust", "glute bridge", "good morning", "clean", "snatch", "back extension", "hyperextension"), "dominante_cadera"),
    (("squat", "lunge", "step up", "step-up", "bulgarian", "split", "leg press", "wall sit", "calf raise", "pistol"), "dominante_rodilla"),
    (("pallof", "anti-rotation", "anti rotation"), "core_antirotacion"),
    (("russian twist", "woodchop", "wood chop", "twist", "rotation"), "core_rotacion"),
    (("side plank", "side bridge", "suitcase"), "core_lateral"),
    (("sit-up", "sit up", "crunch", "leg raise", "knee raise", "v-up", "v up", "toe touch", "flutter kick", "scissor"), "core_flexion_cadera"),
    (("plank", "hollow", "dead bug", "bird dog", "superman", "bridge hold"), "core_antiextension"),
    (("burpee", "jump", "sprint", "skipping", "rope", "mountain climber", "high knees", "jack", "skater", "shuttle"), "acondicionamiento"),
]

# Respaldo por zona corporal / grupo muscular del dataset.
PATRON_POR_ZONA = {
    "chest": "empuje_horizontal",
    "shoulders": "empuje_vertical",
    "back": "tiron_horizontal",
    "upper legs": "dominante_rodilla",
    "lower legs": "dominante_rodilla",
    "waist": "core_antiextension",
    "cardio": "acondicionamiento",
    "neck": "recuperacion",
}
PATRON_POR_GRUPO = {
    "biceps": "tiron_horizontal",
    "forearms": "tiron_horizontal",
    "triceps": "empuje_horizontal",
    "chest": "empuje_horizontal",
    "shoulders": "empuje_vertical",
    "deltoids": "empuje_vertical",
    "lats": "tiron_vertical",
    "latissimus dorsi": "tiron_vertical",
    "traps": "tiron_vertical",
    "trapezius": "tiron_horizontal",
    "quadriceps": "dominante_rodilla",
    "hamstrings": "dominante_cadera",
    "glutes": "dominante_cadera",
    "calves": "dominante_rodilla",
    "core": "core_antiextension",
    "abdominals": "core_flexion_cadera",
    "obliques": "core_rotacion",
}

# Coste por dimensión según patrón (conservador: medio por defecto).
COSTE_POR_PATRON = {
    "empuje_horizontal": {"empuje": "medio", "core": "bajo"},
    "empuje_vertical": {"empuje": "medio", "core": "bajo"},
    "tiron_horizontal": {"tiron": "medio", "agarre": "bajo"},
    "tiron_vertical": {"tiron": "medio", "agarre": "medio"},
    "dominante_rodilla": {"rodilla_piernas": "medio", "core": "bajo"},
    "dominante_cadera": {"bisagra": "medio", "lumbar": "medio", "agarre": "bajo"},
    "core_antiextension": {"core": "medio", "lumbar": "bajo"},
    "core_antirotacion": {"core": "medio"},
    "core_lateral": {"core": "medio"},
    "core_flexion_cadera": {"core": "medio", "lumbar": "bajo"},
    "core_rotacion": {"core": "medio", "lumbar": "medio"},
    "acondicionamiento": {"cardio": "medio", "impacto_articular": "bajo"},
    "agilidad": {"impacto_articular": "medio", "cardio": "bajo"},
    "movilidad_cargada": {"core": "bajo"},
    "recuperacion": {"core": "bajo"},
}

OBJETIVO_POR_PATRON = {
    "empuje_horizontal": "fuerza_resistencia",
    "empuje_vertical": "fuerza_resistencia",
    "tiron_horizontal": "fuerza_resistencia",
    "tiron_vertical": "fuerza_resistencia",
    "dominante_rodilla": "fuerza_resistencia",
    "dominante_cadera": "fuerza",
    "core_antiextension": "estabilidad_lumbopelvica",
    "core_antirotacion": "antirotacion",
    "core_lateral": "estabilidad_lateral",
    "core_flexion_cadera": "core",
    "core_rotacion": "rotacion",
    "acondicionamiento": "acondicionamiento",
    "agilidad": "coordinacion",
    "movilidad_cargada": "movilidad",
    "recuperacion": "recuperacion",
}

# Impacto lumbar: amarillo por defecto (conservador). Rojo ante bisagra
# cargada, hiperextensión o rotación; verde solo tumbado o apoyado sin carga
# axial (peso corporal o goma, nunca kettlebell sobre la cabeza).
PALABRAS_ROJO = ("deadlift", "good morning", "swing", "clean", "snatch", "twist", "rotation", "woodchop", "wood chop", "back extension", "hyperextension", "bent over", "bent-over", "suitcase")
PALABRAS_VERDE = ("lying", "floor", "plank", "dead bug", "glute bridge", "side plank", "bird dog", "superman", "prone", "supine", "crunch", "sit-up", "sit up", "leg raise", "knee raise", "bridge")

PALABRAS_UNILATERAL = ("single", "one arm", "one-arm", "one leg", "one-leg", "single-leg", "single-arm", "alternating", "lunge", "split", "pistol", "step up", "step-up", "bulgarian", "staggered")
PALABRAS_AVANZADO = ("muscle up", "pistol", "handstand", "planche", "lever", "dragon", "nordic", "v-up", "v up")
PALABRAS_AGARRE_BJJ = ("pull up", "pull-up", "pullup", "chin up", "chin-up", "chinup", "row", "deadlift", "swing", "kettlebell", "farmer", "towel", "hang", "rope")
PALABRAS_ISOMETRICO = ("plank", "hold", "hollow", "wall sit", "dead bug", "bird dog", "superman")


def _norm(texto: str) -> str:
    return re.sub(r"\s+", " ", (texto or "").lower()).strip()


def slug_id(nombre_en: str) -> str:
    """Identificador kebab-case en inglés a partir del nombre del dataset."""
    texto = unicodedata.normalize("NFKD", nombre_en).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return re.sub(r"-{2,}", "-", texto) or "ejercicio"


def inferir_patron(nombre: str, body_part: str, muscle_group: str) -> str:
    n = _norm(nombre)
    for claves, patron in _REGLAS_PATRON:
        if any(c in n for c in claves):
            return patron
    if body_part in ("upper arms", "lower arms"):
        return PATRON_POR_GRUPO.get(_norm(muscle_group), "tiron_horizontal")
    return PATRON_POR_ZONA.get(_norm(body_part), "acondicionamiento")


def inferir_impacto_lumbar(nombre: str, equipment: str) -> str:
    n = _norm(nombre)
    if any(p in n for p in PALABRAS_ROJO):
        return "rojo"
    if any(p in n for p in PALABRAS_VERDE) and equipment in ("body weight", "band", "resistance band"):
        return "verde"
    return "amarillo"


def inferir_etiquetas(registro: dict, material: list[str]) -> dict:
    """Borrador de catalogación fitlosophy para un ejercicio del dataset."""
    nombre = registro.get("name") or ""
    body_part = registro.get("body_part") or ""
    grupo = registro.get("muscle_group") or ""
    equipment = registro.get("equipment") or ""
    n = _norm(nombre)

    patron = inferir_patron(nombre, body_part, grupo)
    impacto = inferir_impacto_lumbar(nombre, equipment)
    unilateral = any(p in n for p in PALABRAS_UNILATERAL)
    isometrico = any(p in n for p in PALABRAS_ISOMETRICO)
    coste = dict(COSTE_POR_PATRON.get(patron, {"core": "medio"}))
    if equipment == "rope" or _norm(body_part) == "cardio":
        coste = {"cardio": "medio", "impacto_articular": "bajo"}

    if equipment == "rope":
        prescripcion = {"series": [3, 6], "saltos": [50, 100]}
    elif isometrico:
        prescripcion = {"series": [2, 4], "segundos": [20, 45], "evitar_fallo": True}
    else:
        prescripcion = {"series": [3, 4], "repeticiones": [8, 12], "reserva_repeticiones": [2, 3], "evitar_fallo": True}
    if unilateral:
        prescripcion["por_lado"] = True

    descripcion = _descripcion(registro, impacto)

    return {
        "id": slug_id(nombre),
        "patron": patron,
        "secundarios": [],
        "nivel": "avanzado" if any(p in n for p in PALABRAS_AVANZADO) else "base",
        "lateralidad": "unilateral" if unilateral else "bilateral",
        "impacto_lumbar": impacto,
        "compatibilidad_bjj": "limitada" if any(p in n for p in PALABRAS_AGARRE_BJJ) else "si",
        "coste_dimensiones": coste,
        "objetivos": [OBJETIVO_POR_PATRON.get(patron, "control")],
        "prescripcion": prescripcion,
        "descripcion": descripcion,
        "isometrico": isometrico,
    }


def _descripcion(registro: dict, impacto: str) -> str:
    """Una o dos frases de ejecución a partir de las instrucciones en español.

    Si el impacto lumbar inferido es rojo se añade el límite con palabras
    (docs/05), para que la validación determinista no lo rechace.
    """
    pasos = (registro.get("instructions") or {}).get("es") or ""
    frases = [f.strip() for f in re.split(r"(?<=[.!?])\s+", pasos.replace("\n", " ")) if f.strip()]
    desc = " ".join(frases[:2])[:300].strip()
    if impacto == "rojo":
        desc = (desc + " Detén el ejercicio si aparece molestia lumbar.").strip()
    return desc


def equivalente_probable(nombre_en: str, catalogo) -> str | None:
    """Deduplicado heurístico por tokens contra los ids del catálogo estable.

    No bloquea nada: solo marca el candidato con `posible_equivalente` para que
    el revisor lo compare. El id del catálogo está en inglés (convención), así
    que la comparación por tokens caza «push-up» con «pushup-classic».
    """
    tokens = {t for t in slug_id(nombre_en).split("-") if len(t) > 2}
    if not tokens:
        return None
    mejor, mejor_marca = None, 0.0
    for ej in catalogo:
        t_ej = set(ej.id.split("-"))
        comunes = tokens & t_ej
        if not comunes:
            continue
        marca = len(comunes) / max(len(tokens), len(t_ej))
        if marca > mejor_marca:
            mejor, mejor_marca = ej.id, marca
    return mejor if mejor_marca >= 0.5 else None


# --- Entrada definitiva del catálogo -------------------------------------------


def construir_entrada(candidato: dict, etiquetas: dict, ids_existentes: set[str]) -> dict:
    """Entrada de `ejercicios.yaml` a partir del candidato y sus etiquetas.

    `candidato` lleva `nombre_es` y `material_fitlosophy`; `etiquetas` son las
    finales si el revisor editó el borrador o las inferidas si no.
    """
    eid = etiquetas.get("id") or slug_id(candidato["nombre_en"])
    base = eid
    i = 2
    while eid in ids_existentes:
        eid = f"{base}-{i}"
        i += 1

    material = list(candidato.get("material_fitlosophy") or [])
    entrada = {
        "id": eid,
        "nombre": etiquetas.get("nombre") or candidato["nombre_es"],
        "descripcion": etiquetas["descripcion"],
        "patron": etiquetas["patron"],
        "material": material,
        "nivel": etiquetas["nivel"],
        "lateralidad": etiquetas["lateralidad"],
        "coste_dimensiones": etiquetas["coste_dimensiones"],
        "impacto_lumbar": etiquetas["impacto_lumbar"],
        "compatibilidad_bjj": etiquetas["compatibilidad_bjj"],
        "objetivos": etiquetas.get("objetivos") or ["control"],
        "prescripcion": etiquetas["prescripcion"],
    }
    if not material:
        entrada["sin_material"] = True
    if etiquetas.get("secundarios"):
        entrada["secundarios"] = etiquetas["secundarios"]
    if etiquetas.get("isometrico"):
        entrada["isometrico"] = True
    if etiquetas.get("explosivo"):
        entrada["explosivo"] = True
    return entrada


def render_entrada_yaml(entrada: dict) -> str:
    """Bloque YAML de un ejercicio, con la sangría de la lista `exercises`.

    `safe_dump` entrecomilla los valores que YAML 1.1 leería como booleanos
    («si»/«no»), como exige el test del catálogo.
    """
    cuerpo = yaml.safe_dump(entrada, allow_unicode=True, sort_keys=False, width=100)
    lineas = cuerpo.rstrip("\n").split("\n")
    return "\n  - " + lineas[0] + "".join("\n    " + ln for ln in lineas[1:]) + "\n"
