"""Cabeceras de caché del frontend compilado (fitlosophy_api.static).

Sin `Cache-Control`, el CDN y el navegador cachean por heurística y un
`index.html` viejo sigue apuntando a los JS/CSS de la compilación anterior: los
cambios no llegan al usuario. Estos tests fijan la política.
"""

import pytest
from fastapi.testclient import TestClient

from fitlosophy_api.app import create_app
from fitlosophy_api.static import CACHE_INMUTABLE, CACHE_REVALIDAR


@pytest.fixture()
def app_con_dist(tmp_path, monkeypatch):
    """Aplicación con un `dist` simulado con la forma que genera Vite."""
    dist = tmp_path / "frontend" / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text(
        '<!doctype html><script src="/assets/index-BcWrwx67.js"></script>', encoding="utf-8"
    )
    (dist / "assets" / "index-BcWrwx67.js").write_text("console.log(1)", encoding="utf-8")
    (dist / "favicon.svg").write_text("<svg/>", encoding="utf-8")

    # create_app localiza dist como parents[3]/frontend/dist desde el módulo.
    import fitlosophy_api.app as modulo

    monkeypatch.setattr(modulo, "__file__", str(tmp_path / "backend" / "src" / "api" / "app.py"))
    return create_app(tmp_path / "test.db")


def test_index_se_revalida_siempre(app_con_dist):
    """El nombre de index.html no cambia entre compilaciones: nunca se reutiliza
    sin preguntar al origen."""
    with TestClient(app_con_dist) as c:
        for ruta in ("/", "/index.html"):
            r = c.get(ruta)
            assert r.status_code == 200, ruta
            assert r.headers["cache-control"] == CACHE_REVALIDAR, ruta


def test_los_assets_con_hash_son_inmutables(app_con_dist):
    """El hash del nombre ya identifica la versión: cachear para siempre es
    seguro y hace innecesario cualquier `?v=`."""
    with TestClient(app_con_dist) as c:
        r = c.get("/assets/index-BcWrwx67.js")
        assert r.status_code == 200
        assert r.headers["cache-control"] == CACHE_INMUTABLE


def test_los_ficheros_de_nombre_fijo_se_revalidan(app_con_dist):
    """favicon, iconos y demás de public/ conservan el nombre: como index.html."""
    with TestClient(app_con_dist) as c:
        r = c.get("/favicon.svg")
        assert r.status_code == 200
        assert r.headers["cache-control"] == CACHE_REVALIDAR


def test_la_revalidacion_devuelve_304(app_con_dist):
    """El coste de `no-cache` es una petición condicional, no una descarga."""
    with TestClient(app_con_dist) as c:
        r = c.get("/")
        etag = r.headers["etag"]
        r2 = c.get("/", headers={"If-None-Match": etag})
        assert r2.status_code == 304
        assert r2.headers["cache-control"] == CACHE_REVALIDAR
