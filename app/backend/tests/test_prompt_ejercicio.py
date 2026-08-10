"""El prompt de ejercicio nuevo no puede desincronizarse del catálogo.

`docs/roles/prompt-ejercicio-nuevo.md` lleva embebidos los vocabularios
cerrados y el inventario de material para que el agente externo no invente
valores. Si se amplía un dominio en `data/ejercicios.yaml` y nadie actualiza el
prompt, el agente seguiría proponiendo con el vocabulario viejo y el fallo
aparecería tarde, en forma de propuestas rechazadas por el validador.
"""

from pathlib import Path

import pytest

from fitlosophy.catalog import MATERIAL_A_PERFIL, load_default_catalog

PROMPT = Path(__file__).resolve().parents[3] / "docs" / "roles" / "prompt-ejercicio-nuevo.md"


@pytest.fixture(scope="module")
def texto():
    return PROMPT.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "dominio",
    ["patron", "dimensiones", "nivel_coste", "impacto_lumbar", "compatibilidad_bjj", "nivel", "lateralidad"],
)
def test_el_prompt_enumera_los_dominios_vigentes(texto, dominio):
    for valor in load_default_catalog().valores[dominio]:
        assert f"`{valor}`" in texto, f"«{valor}» ({dominio}) falta en el prompt"


def test_el_prompt_enumera_el_material_disponible(texto):
    for token in MATERIAL_A_PERFIL:
        assert f"`{token}`" in texto, f"el material «{token}» falta en el prompt"


def test_el_prompt_conserva_la_puerta_de_seguridad_lumbar(texto):
    """Un agente leyendo un vídeo no conoce los episodios lumbares del atleta:
    la instrucción de no proponer «verde» es la que evita que se cuele."""
    assert "nunca propongas `impacto_lumbar: verde`" in texto
