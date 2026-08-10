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


def test_los_valores_categoricos_son_texto(catalogo):
    """YAML 1.1 convierte `no` en el booleano False.

    `compatibilidad_bjj: no` se leía como `False`, así que una comparación
    futura del tipo `ej.compatibilidad_bjj == "no"` nunca habría casado — y ese
    valor marca justo los ejercicios que no deben programarse antes de BJJ. Los
    valores del dominio van entrecomillados en el YAML; esto lo vigila.
    """
    for e in catalogo:
        assert isinstance(e.compatibilidad_bjj, str), f"{e.id}: {e.compatibilidad_bjj!r}"
        assert isinstance(e.impacto_lumbar, str), f"{e.id}: {e.impacto_lumbar!r}"
        assert isinstance(e.nivel, str) and isinstance(e.lateralidad, str), e.id

    for dominio in ("compatibilidad_bjj", "impacto_lumbar", "nivel", "lateralidad", "patron"):
        for valor in catalogo.valores[dominio]:
            assert isinstance(valor, str), f"valores.{dominio}: {valor!r}"


def test_los_valores_de_los_ejercicios_estan_en_su_dominio(catalogo):
    """Cierra el círculo del validador: lo que ya está dentro también cumple."""
    val = catalogo.valores
    for e in catalogo:
        assert e.patron in val["patron"], e.id
        assert e.impacto_lumbar in val["impacto_lumbar"], e.id
        assert e.compatibilidad_bjj in val["compatibilidad_bjj"], e.id
        assert e.nivel in val["nivel"], e.id
        assert e.lateralidad in val["lateralidad"], e.id
        for dim, nivel in e.coste_dimensiones.items():
            assert dim in val["dimensiones"], f"{e.id}: {dim}"
            assert nivel in val["nivel_coste"], f"{e.id}: {dim}={nivel}"
