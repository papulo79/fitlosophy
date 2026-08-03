# Fitlosophy — backend

Motor de decisión, generador de sesiones y API del MVP (`docs/14`) del sistema
Fitlosophy. La especificación del dominio vive en `../../docs/` (03, 06, 12, 14)
y los datos en `../../data/`.

## Estructura

```text
app/backend/
├── pyproject.toml
├── scripts/
│   └── init_db.py          # inicializa la BD y crea el usuario único
├── src/
│   ├── fitlosophy/         # núcleo del dominio (sin dependencias web)
│   │   ├── catalog.py      # carga de data/ejercicios.yaml y data/perfil.yaml
│   │   ├── models.py       # entidades (dataclasses)
│   │   ├── load.py         # carga activa por dimensiones (docs/12)
│   │   ├── engine.py       # motor de decisión D/C/P (docs/03)
│   │   └── generator.py    # generador de sesiones (docs/06)
│   └── fitlosophy_api/     # capa HTTP del MVP (docs/14)
│       ├── app.py          # fábrica FastAPI (create_app)
│       ├── db.py           # esquema SQLite (stdlib sqlite3)
│       ├── auth.py         # usuario único, pbkdf2, cookie de sesión 30 días
│       ├── history.py      # historial persistido → eventos del motor
│       ├── schemas.py      # entradas validadas (pydantic)
│       └── routes.py       # endpoints del flujo diario
└── tests/
    ├── test_load.py        # modelo de carga (docs/12)
    ├── test_cases.py       # los 10 casos de docs/13 (criterio 1)
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

## Inicializar la base de datos

El usuario único se crea desde variables de entorno (no hay registro, docs/14):

```bash
FITLOSOPHY_USER=mi_usuario FITLOSOPHY_PASSWORD=mi_contraseña \
  PYTHONPATH=src python3 scripts/init_db.py
```

Opcional: `FITLOSOPHY_DB` fija la ruta de la BD (por defecto `./fitlosophy.db`).
El script también siembra el perfil editable desde `../../data/perfil.yaml`.

## Lanzar el servidor

```bash
cd app/backend
PYTHONPATH=src FITLOSOPHY_DB=fitlosophy.db \
  uvicorn "fitlosophy_api.app:create_app" --factory --host 127.0.0.1 --port 8000
```

Documentación interactiva en `http://127.0.0.1:8000/docs`.

## Ejecutar los tests

```bash
cd app/backend
python3 -m pytest          # toda la suite (núcleo + casos docs/13 + API)
python3 -m pytest tests/test_api.py
```

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
