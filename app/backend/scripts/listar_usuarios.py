"""Lista los usuarios del despliegue y su actividad.

Para saber quién hay dado de alta sin abrir la base de datos a mano. No muestra
ningún dato de entrenamiento: solo el recuento, porque el historial de cada uno
es suyo (docs/14).

Uso:
    cd app/backend
    ./.venv/bin/python scripts/listar_usuarios.py
"""

from __future__ import annotations

from _comun import abrir_bd, ejecutar

from fitlosophy_api.usuarios import listar_usuarios  # noqa: E402


def main() -> int:
    conn, ruta = abrir_bd()
    usuarios = listar_usuarios(conn)
    if not usuarios:
        print(f"No hay ningún usuario en {ruta}. Crea uno con scripts/crear_usuario.py.")
        return 0

    print(f"{len(usuarios)} usuario(s) en {ruta}:\n")
    cabecera = f"{'id':>3}  {'usuario':<20} {'alta':<12} {'sesiones':>8} {'entrenos':>8} {'bjj':>5}  último entreno"
    print(cabecera)
    print("-" * len(cabecera))
    for u in usuarios:
        ultimo = (u["ultimo_entreno"] or "—")[:10]
        print(
            f"{u['id']:>3}  {u['username']:<20} {u['created_at'][:10]:<12} "
            f"{u['sesiones_abiertas']:>8} {u['entrenos']:>8} {u['bjj']:>5}  {ultimo}"
        )
    print("\n«sesiones» son las cookies de acceso abiertas y sin caducar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
