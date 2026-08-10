"""Tests del cargador de `.env` (fitlosophy_api.config)."""

import os

from fitlosophy_api.config import cargar_env, leer_bool, leer_int


def test_carga_claves_del_fichero(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text(
        "\n".join(
            [
                "# comentario",
                "",
                "FITLOSOPHY_DB=prueba.db",
                "  export FITLOSOPHY_USER = atleta  ",
                'FITLOSOPHY_PASSWORD="con espacios"',
                "SIN_IGUAL",
                "FITLOSOPHY_COOKIE_SECURE='true'",
            ]
        ),
        encoding="utf-8",
    )
    for clave in ("FITLOSOPHY_DB", "FITLOSOPHY_USER", "FITLOSOPHY_PASSWORD", "FITLOSOPHY_COOKIE_SECURE"):
        monkeypatch.delenv(clave, raising=False)

    aplicadas = cargar_env(env)

    assert aplicadas["FITLOSOPHY_DB"] == "prueba.db"
    assert os.environ["FITLOSOPHY_USER"] == "atleta"  # `export` y espacios
    assert os.environ["FITLOSOPHY_PASSWORD"] == "con espacios"  # comillas fuera
    assert leer_bool("FITLOSOPHY_COOKIE_SECURE") is True
    assert "SIN_IGUAL" not in aplicadas  # línea malformada ignorada


def test_el_entorno_gana_sobre_el_fichero(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("FITLOSOPHY_DB=del-fichero.db\n", encoding="utf-8")
    monkeypatch.setenv("FITLOSOPHY_DB", "del-entorno.db")

    aplicadas = cargar_env(env)

    assert os.environ["FITLOSOPHY_DB"] == "del-entorno.db"
    assert "FITLOSOPHY_DB" not in aplicadas


def test_fichero_inexistente_no_falla(tmp_path):
    assert cargar_env(tmp_path / "no-existe") == {}


def test_lectores_con_valores_invalidos(monkeypatch):
    monkeypatch.setenv("X_INT", "no-es-un-numero")
    monkeypatch.setenv("X_BOOL", "sí")
    assert leer_int("X_INT", 7) == 7
    assert leer_int("X_AUSENTE", 5) == 5
    assert leer_bool("X_BOOL") is True
    assert leer_bool("X_AUSENTE", True) is True
