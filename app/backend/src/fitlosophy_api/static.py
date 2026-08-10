"""Servido del frontend compilado con política de caché explícita.

Sin esto, `StaticFiles` responde solo con `ETag` y `Last-Modified`, sin ningún
`Cache-Control`: navegador y CDN quedan libres para cachear por heurística. En
un despliegue tras un túnel de Cloudflare eso significa que un `index.html`
viejo sigue sirviéndose durante horas y apunta a los ficheros JS/CSS de la
compilación anterior — los cambios no se ven en remoto aunque el servidor ya
tenga el código nuevo.

La política aprovecha lo que Vite ya hace:

- `assets/` contiene ficheros con hash de contenido en el nombre
  (`index-BcWrwx67.js`). Si el contenido cambia, cambia la URL, así que se
  pueden cachear para siempre: `immutable`. Añadirles un `?v=` sería redundante.
- Todo lo demás (`index.html`, `favicon.svg`, `icono-*.png`) conserva un nombre
  fijo entre compilaciones. Ahí es donde se pega el caché, y por eso van con
  `no-cache`: obliga a revalidar antes de usar. Con el `ETag` que ya envía
  `StaticFiles`, la revalidación normal es un 304 sin cuerpo.

`no-cache` no significa «no cachear» (eso es `no-store`), sino «no reutilizar
sin preguntar». El coste por carga es una petición condicional.
"""

from __future__ import annotations

from starlette.staticfiles import StaticFiles

# Ficheros con hash de contenido en el nombre: la URL ya identifica la versión.
CACHE_INMUTABLE = "public, max-age=31536000, immutable"
# Nombres estables: revalidar siempre contra el origen.
CACHE_REVALIDAR = "no-cache, must-revalidate"

PREFIJO_CON_HASH = "assets/"


class EstaticosVersionados(StaticFiles):
    """`StaticFiles` que declara la caducidad de cada fichero según su nombre."""

    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        # `path` llega normalizado y relativo al directorio servido; para «/»
        # no apunta todavía a index.html, pero cae en la rama conservadora.
        con_hash = path.replace("\\", "/").startswith(PREFIJO_CON_HASH)
        response.headers["Cache-Control"] = CACHE_INMUTABLE if con_hash else CACHE_REVALIDAR
        return response
