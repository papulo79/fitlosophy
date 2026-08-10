"""Integridad del catálogo de ejercicios (docs/05).

Las reglas de la sección «Ejecución» de `docs/05` no se pueden verificar leyendo
el YAML a ojo con 28 ejercicios y creciendo: aquí quedan como pruebas.
"""

import pytest

from fitlosophy.catalog import load_default_catalog


@pytest.fixture(scope="module")
def catalogo():
    return load_default_catalog()


def test_todos_los_ejercicios_tienen_descripcion(catalogo):
    """docs/05: `descripcion` es obligatoria. Sin ella la pantalla solo puede
    mostrar el nombre y la dosis, que fue justo el problema que la motivó."""
    sin_descripcion = [e.id for e in catalogo if not e.descripcion.strip()]
    assert sin_descripcion == []


def test_la_descripcion_no_repite_el_nombre_ni_la_dosis(catalogo):
    """docs/05, criterio 2: la dosis sale de `prescripcion`; duplicarla en el
    texto las desincronizaría al primer ajuste."""
    for e in catalogo:
        assert not e.descripcion.lower().startswith(e.nombre.lower()), e.id
        assert "×" not in e.descripcion, e.id


def test_la_dosis_por_patron_exige_enumerar_los_patrones(catalogo):
    """docs/05, criterio 3: «4 pasadas» sin la lista de patrones es una dosis
    que el usuario no puede ejecutar."""
    for e in catalogo:
        if "pasadas_por_patron" in e.prescripcion:
            assert e.patrones, f"{e.id} dosifica por patrón sin enumerarlos"


def test_los_patrones_solo_donde_la_dosis_los_usa(catalogo):
    """A la inversa: enumerar patrones sin dosis por patrón dejaría una lista
    sin cifra que aplicarle."""
    for e in catalogo:
        if e.patrones:
            assert "pasadas_por_patron" in e.prescripcion, e.id


def test_los_ejercicios_de_riesgo_declaran_su_limite_en_palabras(catalogo):
    """docs/05, criterio 1: quien lee la descripción en el móvil no ve la
    etiqueta `impacto_lumbar`, así que el aviso tiene que estar en el texto."""
    señales = ("lumbar", "espalda", "rotación", "molestia", "despacio")
    for e in catalogo:
        if e.impacto_lumbar == "rojo":
            texto = e.descripcion.lower()
            assert any(s in texto for s in señales), e.id
