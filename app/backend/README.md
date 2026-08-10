# Fitlosophy — backend

Motor de decisión, generador de sesiones y API del MVP (`docs/14`) del sistema
Fitlosophy. La especificación del dominio vive en `../../docs/` (03, 06, 12, 14)
y los datos en `../../data/`.

## Estructura

```text
app/backend/
├── pyproject.toml
├── .env.example            # plantilla de configuración (el .env real no se versiona)
├── scripts/
│   ├── init_db.py          # inicializa la BD y crea el usuario único
│   └── cambiar_password.py # rota la contraseña e invalida las sesiones
├── src/
│   ├── fitlosophy/         # núcleo del dominio (sin dependencias web)
│   │   ├── catalog.py      # carga de data/ejercicios.yaml y data/perfil.yaml
│   │   ├── models.py       # entidades (dataclasses)
│   │   ├── load.py         # carga activa por dimensiones (docs/12)
│   │   ├── engine.py       # motor de decisión D/C/P (docs/03)
│   │   └── generator.py    # generador de sesiones (docs/06)
│   └── fitlosophy_api/     # capa HTTP del MVP (docs/14)
│       ├── app.py          # fábrica FastAPI (create_app)
│       ├── config.py       # variables de entorno con respaldo en .env
│       ├── db.py           # esquema SQLite (stdlib sqlite3)
│       ├── auth.py         # usuario único, pbkdf2, cookie 30 días, freno de fuerza bruta
│       ├── history.py      # historial persistido → eventos del motor
│       ├── schemas.py      # entradas validadas (pydantic)
│       └── routes.py       # endpoints del flujo diario
└── tests/
    ├── test_load.py        # modelo de carga (docs/12)
    ├── test_cases.py       # los 10 casos de docs/13 (criterio 1)
    ├── test_config.py      # cargador de .env
    └── test_api.py         # flujo extremo a extremo de la API
```

## Instalación

```bash
cd app/backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

También funciona sin instalar el paquete: los tests añaden `src/` al path
(`tests/conftest.py`) y para el servidor basta `PYTHONPATH=src`.

## Configuración (`.env`)

Toda la configuración del despliegue son variables de entorno con respaldo en
`app/backend/.env`, que **no se versiona** (contiene la contraseña y la ruta de
una BD con datos personales de salud). Parte de la plantilla:

```bash
cd app/backend
cp .env.example .env      # y rellena los valores
```

Precedencia: **variable ya presente en el entorno > `.env` > valor por defecto**.
Así un `FITLOSOPHY_DB=otra.db uvicorn ...` puntual sigue ganando sobre el
fichero, y los tests no dependen del `.env` local (`tests/conftest.py` lo
desactiva a propósito). `FITLOSOPHY_ENV_FILE` permite apuntar a otra ruta.

Las claves están documentadas una a una en `.env.example`: ruta de la BD,
usuario y contraseña iniciales, `FITLOSOPHY_COOKIE_SECURE` y los umbrales del
freno de fuerza bruta.

## Inicializar la base de datos

El usuario único se crea una sola vez (no hay registro, docs/14). Con el `.env`
relleno basta:

```bash
cd app/backend
./.venv/bin/python scripts/init_db.py
```

O pasando las credenciales a mano, sin tocar el `.env`:

```bash
FITLOSOPHY_USER=mi_usuario FITLOSOPHY_PASSWORD=mi_contraseña \
  ./.venv/bin/python scripts/init_db.py
```

Si la BD ya tiene usuario, el script **no lo toca ni cambia la contraseña**: lo
dice por pantalla y termina bien, así que es fácil creer que la ha cambiado
cuando no. Para rotarla:

```bash
cd app/backend
# con la contraseña nueva en FITLOSOPHY_PASSWORD del .env
./.venv/bin/python scripts/cambiar_password.py
```

Además de actualizar el hash, **invalida todas las sesiones abiertas** y limpia
los intentos fallidos: una contraseña se rota porque la anterior ya no es de
fiar, y las cookies emitidas con ella durarían 30 días más. Hay que volver a
entrar en todos los dispositivos.

Las contraseñas se guardan con hash pbkdf2-sha256 y salt: **no son
recuperables**. El script siembra también el perfil editable desde
`../../data/perfil.yaml`.

## Lanzar el servidor

```bash
cd app/backend
./.venv/bin/uvicorn "fitlosophy_api.app:create_app" --factory --host 127.0.0.1 --port 10012
```

Documentación interactiva en `http://127.0.0.1:10012/docs`. Si existe
`../frontend/dist`, la misma URL sirve además el frontend compilado.

Detrás de un proxy inverso o de un túnel (Cloudflare), añade
`--proxy-headers --forwarded-allow-ips 127.0.0.1` para que la IP del cliente
que ve el freno de fuerza bruta sea la real y no la del proxy.

## Desplegar una actualización

Desde la raíz del repositorio, un solo comando:

```bash
./scripts/desplegar.sh
```

Hace, en orden: recompila el frontend (`npm run build`), reinicia el servicio
systemd, espera a que responda, comprueba que la cabecera de caché sigue puesta
y, si hay `CLOUDFLARE_API_TOKEN` y `CLOUDFLARE_ZONE_ID` en el `.env`, purga el
caché del borde.

**Recompilar no es opcional**: el backend sirve `app/frontend/dist`, así que un
cambio en Svelte que no se compile no llega a la URL por mucho que reinicies el
servicio. Ese fue el origen de los cambios que «no se reflejaban» en remoto.

Cuándo hace falta algo más que este comando:

| Cambio | Además de `desplegar.sh` |
|---|---|
| Código Python o Svelte | nada |
| `data/*.yaml` | nada: el catálogo se recarga al arrancar el servicio |
| Claves del `.env` | nada: las lee la aplicación al arrancar |
| `FITLOSOPHY_HOST` / `PORT` | `systemctl --user daemon-reload` (los lee systemd) |
| Fichero `.service` | `systemctl --user daemon-reload` |
| Esquema de la BD | nada: `crear_esquema` usa `CREATE TABLE IF NOT EXISTS` |
| Puerto nuevo | regla de ufw y `service` del túnel en el panel |

Antes de desplegar, la suite: `./.venv/bin/python -m pytest`.

## Despliegue: red y cortafuegos

El servicio corre en el host (systemd, no en Docker) y escucha en
`${FITLOSOPHY_HOST}:${FITLOSOPHY_PORT}` — hoy `0.0.0.0:10012` — porque tiene dos
consumidores:

- La **LAN**, en `http://192.168.1.145:10012`.
- El contenedor de **cloudflared**, que gestiona el túnel desde el panel de
  Cloudflare (sin `config.yml` local). Desde dentro del contenedor, el host es
  el gateway de su red `bridge`: el *service* del túnel apunta a
  `http://172.17.0.1:10012`.

Con **ufw activo hacen falta dos reglas**. Los puertos publicados por
contenedores esquivan ufw, pero un servicio del host pasa por `INPUT` y se
bloquea; el síntoma es un *timeout* desde el contenedor mientras desde el
propio host responde 200:

```bash
sudo ufw allow from 192.168.1.0/24 to any port 10012 proto tcp comment 'fitlosophy LAN'
sudo ufw allow in on docker0 to any port 10012 proto tcp comment 'fitlosophy cloudflared'
```

Comprobación de que el contenedor alcanza el host:

```bash
docker run --rm --network bridge curlimages/curl -sS -o /dev/null \
  -w '%{http_code}\n' http://172.17.0.1:10012/
```

Como el puerto queda abierto en la LAN, dos detalles del que depende la
seguridad del login:

- `FITLOSOPHY_COOKIE_SECURE=auto` marca la cookie `Secure` solo cuando la
  petición llega por HTTPS. Por el túnel va protegida; por HTTP en la LAN no,
  porque el navegador descartaría una cookie `Secure` y el login no
  funcionaría. Se puede forzar con `true`/`false`.
- `FITLOSOPHY_PROXIES_CONFIABLES` limita quién puede declarar la IP de origen
  con `CF-Connecting-IP`. Solo loopback y la red de Docker: desde la LAN esa
  cabecera se ignora, de modo que nadie pueda ir cambiándola para esquivar el
  freno de fuerza bruta.

Por lo mismo, `--forwarded-allow-ips` del servicio systemd incluye
`172.17.0.0/16`: cloudflared llega desde ahí, no desde loopback, y sin ello
uvicorn ignoraría `X-Forwarded-Proto` y la cookie nunca se marcaría `Secure`.

## Caché del frontend

`StaticFiles` no envía ningún `Cache-Control`, así que navegador y CDN cachean
por heurística: tras recompilar, el túnel puede seguir sirviendo un
`index.html` viejo que apunta a los JS/CSS de la compilación anterior y los
cambios no se ven. `static.py` fija la política, apoyándose en lo que Vite ya
hace:

| Ruta | Nombre | `Cache-Control` |
|---|---|---|
| `/assets/*` | con hash de contenido (`index-BcWrwx67.js`) | `public, max-age=31536000, immutable` |
| `/`, `/index.html`, `favicon.svg`, `icono-*.png` | fijo entre compilaciones | `no-cache, must-revalidate` |

Como los ficheros de `assets/` cambian de nombre cuando cambia su contenido,
**añadirles un `?v=` es redundante**: la URL ya identifica la versión. Lo que
necesita revalidarse es lo de nombre fijo, y de eso se encarga `no-cache`, que
no significa «no cachear» sino «no reutilizar sin preguntar» (la revalidación
normal es un 304 sin cuerpo).

Por eso el despliegue nunca es solo reiniciar el servicio: hay que **recompilar
el frontend**, o el `dist/` servido seguirá siendo el anterior. De eso se ocupa
`./scripts/desplegar.sh` (ver «Desplegar una actualización»).

## Protección del login

El acceso es de un único usuario sin registro, así que el login es el punto
expuesto. Además del hash pbkdf2 (200 000 iteraciones), `auth.py` frena los
intentos por fuerza bruta con dos umbrales:

- **Por IP**: 5 fallos en 15 min bloquean esa IP durante 15 min, y la duración
  se duplica por cada tanda acumulada en 24 h hasta un techo de 1 h. Durante el
  bloqueo se rechaza incluso la contraseña correcta (HTTP 429 con
  `Retry-After`); un intento rechazado no alarga el bloqueo.
- **Global**: 50 fallos en 15 min desde cualquier conjunto de IPs frenan el
  login por completo. Cubre el ataque repartido, que el límite por IP no vería.

Un login correcto borra los fallos de esa IP. Los umbrales se ajustan por
`.env` y los fallos viven en la tabla `login_failures`, que se purga a las 48 h.

Esto es una defensa de fondo, no un sustituto de poner **Cloudflare Access**
delante si la aplicación se publica en internet.

## Ejecutar los tests

```bash
cd app/backend
./.venv/bin/python -m pytest          # toda la suite (núcleo + casos docs/13 + API)
./.venv/bin/python -m pytest tests/test_api.py
```

Los tests de la API necesitan `httpx2` (lo exige `starlette.testclient`), que
va en el extra `dev` de `pyproject.toml`.

## Uso básico de la API

1. `POST /api/auth/login` → cookie de sesión (30 días, HttpOnly).
2. `POST /api/estado-diario` → propuesta del día (familia, explicación, ítems).
3. `POST /api/propuestas/{id}/sustituir` → cambio de ítem validado (docs/06).
4. `POST /api/sesiones` → aceptar y empezar (ítems marcables).
5. `PATCH /api/sesiones/{id}/items/{item_id}` → completado / modificado /
   sustituido / no_realizado.
6. `POST /api/sesiones/{id}/finalizar` → RPE real; recalcula el impacto con la
   dosis real (los ítems sin marcar cuentan como completados).
7. `POST /api/sesiones/{id}/cierre` → sensación + molestias; una molestia
   congela 24 h la ventana de la dimensión afectada (docs/12).
8. `GET /api/historial`, `GET /api/historial/{fecha}`, `POST /api/bjj`,
   correcciones con `PUT`, `GET/PUT /api/perfil`, `GET /api/export`.

Todo el texto visible está en español y los valores de dominio son los de los
YAML (`verde`, `normal`, `dominante_cadera`...).
