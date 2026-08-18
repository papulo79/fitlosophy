# Changelog

## 0.25.0 - Proceso garantista para ejercicios candidatos

- Nuevo `docs/15-incorporacion-de-ejercicios-candidatos.md`: separa la biblioteca estable del registro de investigación, define extracción desde fuentes arbitrarias, deduplicación mecánica, dossier trazable, puerta de evidencia, revisión independiente y prueba experimental conservadora.
- Nuevo `data/candidatos.yaml`: un fichero deliberadamente separado que el motor no lee. Sus cuatro estados impiden que una sugerencia de un vídeo se convierta en una propuesta automática.
- Nuevos roles `analista-candidatos.md` y `revisor-candidatos.md`: guardarraíles para LLMs, con prohibición de inventar datos, aprobar por sí mismos, recibir información personal o editar el catálogo estable.
- `prompt-ejercicio-nuevo.md` deja de ser la entrada desde una transcripción: ahora solo transforma en YAML un candidato ya revisado. La validación determinista y la aprobación humana siguen siendo obligatorias para la promoción.

## 0.24.0 - Multiusuario: uso familiar con historiales aislados

La aplicación pasa de ser de un único atleta a soportar varios en el mismo despliegue, cada uno con su usuario, su perfil, su historial y sus propuestas. `docs/14` decía lo contrario en tres sitios; se reescribe primero la documentación y después el código, como exige `AGENTS.md`.

**Documentación (primero)**

- `docs/14`, «Acceso y privacidad» reescrita: despliegue familiar, cada usuario es un sistema independiente, sin registro ni gestión de cuentas por HTTP, y un recurso ajeno responde 404 y no 403 —un 403 confirmaría que ese identificador pertenece a alguien—. **Criterio de aceptación 10 nuevo**: ningún usuario puede leer ni modificar datos de otro. El invariante de «una sola sesión activa» se declara individual.
- `docs/11`: entidad **Usuario**, dueña de perfil, estados diarios, propuestas, sesiones y BJJ. No es dueña de la biblioteca de ejercicios, que es común al despliegue.
- `docs/10`: la Fase 9 anota que las muestras de calibración son de personas distintas y **no se agregan**.

**Esquema y migración**

- `user_id NOT NULL REFERENCES users(id)` en `daily_states`, `proposals`, `training_sessions` y `bjj_records`. `session_items` y `session_closures` no lo repiten: cuelgan de su sesión, y duplicar el dueño abriría la puerta a que las dos columnas discrepen.
- `profile` (fila única con `CHECK (id = 1)`) pasa a `profiles`, con una fila por usuario.
- SQLite no admite añadir con `ALTER TABLE` una columna que sea a la vez `NOT NULL` y `REFERENCES`, así que la migración **reconstruye** las tablas con su definición definitiva conservando los identificadores, en vez de dejar la columna anulable: una base de datos migrada y una recién creada quedan con el mismo esquema, y hay un test que lo compara. Es idempotente y verifica `foreign_key_check` al terminar. Si encuentra datos y ningún usuario al que asignárselos, aborta con un mensaje claro en lugar de inventar un dueño.
- Las definiciones de tabla viven ahora en un diccionario `TABLAS` en vez de en un bloque de SQL suelto: la migración necesita la misma definición que usa una base de datos nueva, y con dos copias del `CREATE TABLE` acabarían divergiendo.
- Índices por `(user_id, fecha)` en las cuatro tablas, más `(username, ts)` en `login_failures`.

**Aislamiento (criterio 10)**

- Helpers de propiedad `_sesion_propia`, `_propuesta_propia`, `_bjj_propio` e `_item_de_sesion`: los 13 endpoints con identificador en la ruta pasan por ellos.
- Corregidas las consultas globales, que no eran solo un problema de privacidad: `_sesion_activa` habría hecho que **la primera persona en empezar a entrenar bloqueara a todas las demás**; el `UPDATE ... SET estado = 'descartada'` de `_guardar_propuesta` habría descartado las propuestas de todos al declarar uno su estado diario; `/api/hoy` habría llevado a cerrar la sesión de otro. Y sobre todo `construir_historial`: **la carga activa de cada atleta habría incluido los entrenamientos de los demás**, con propuestas sistemáticamente reducidas por trabajo ajeno.
- `GET /api/export` filtra las siete tablas por usuario e incluye a quién pertenece la copia.
- El núcleo `fitlosophy/` no ha necesitado un solo cambio: `decide`, `generate` y `compute_load` ya recibían historial y material por parámetro. El aislamiento vive entero en `fitlosophy_api/`.

**Alta de usuarios: solo por SSH**

- Nuevo `fitlosophy_api/usuarios.py` y tres scripts: `crear_usuario.py`, `listar_usuarios.py` y `cambiar_password.py` (que ahora recibe el usuario como argumento). La API **no expone ninguna operación de gestión de cuentas**: la superficie que no existe no se puede atacar.
- La contraseña se pide por terminal con `getpass`, dos veces, mínimo 12 caracteres. No se pasa como argumento —`argv` lo ve cualquier proceso con `ps`— ni se guarda en el `.env`. `FITLOSOPHY_USER`/`FITLOSOPHY_PASSWORD` quedan solo para crear el primer usuario de un despliegue nuevo.
- Nuevo `data/perfil-plantilla.yaml`: perfil inicial con el material del lugar de entrenamiento —que se comparte y es lo único del perfil que lee el motor, junto con `bjj.sesiones_semana.min`— y el resto vacío. El perfil de un atleta nunca se copia a otro. `init_db.py` deja de sembrar un perfil global.
- `perfil_desde_dict` tolera valores nulos en `bjj.sesiones_semana.min`: con la plantilla, un campo sin rellenar ya no puede reventar la decisión del día.

**Freno de fuerza bruta por usuario**

- Tercer umbral, por `username` (10 fallos en la ventana, mismo escalado): cubre el ataque repartido entre muchas IPs contra una contraseña concreta, que el límite por IP no veía. El precio, documentado, es que quien conozca un nombre de usuario puede bloquear a esa persona mientras dure; por eso el umbral es el doble que el de IP. Un login correcto limpia los fallos de esa IP **y** los de esa cuenta.

**Concurrencia**

- **Una conexión SQLite por petición** en lugar de una única conexión compartida cuyo lock global se mantenía tomado durante toda la petición: el servidor atendía a una persona cada vez, y declarar el estado diario reconstruye el historial y ejecuta motor y generador. Además cada petición tiene ahora su propia transacción, así que un fallo a mitad no puede confirmar el trabajo a medias de otra. Con `journal_mode = WAL` los lectores no esperan al escritor y `busy_timeout` evita el «database is locked».
- `db_conn` se muda a `db.py` para que `auth.py` pueda depender de ella sin ciclo de importación; `usuario_actual` la recibe por dependencia.

**Tests**

- Nuevo `tests/test_multiusuario.py` (17 tests): 404 cruzado en los 13 endpoints con id, el historial del motor solo ve lo propio, dos pueden entrenar a la vez, redeclarar el estado no descarta la propuesta ajena, `/api/hoy` no arrastra el cierre pendiente de otro, exportación y perfiles independientes, freno por usuario, y la migración desde el esquema antiguo —con su esquema literal— comprobando dueños, identificadores conservados, idempotencia y equivalencia con una base de datos nueva.
- **Corregida una contaminación entre módulos de la propia suite**: `config.cargar_env` escribe en `os.environ` a propósito y `monkeypatch` no puede deshacer esa escritura, así que `FITLOSOPHY_COOKIE_SECURE=true` se filtraba desde los tests del cargador a todo lo que corriera después, marcando la cookie como `Secure` sobre HTTP y dejando sin sesión a los tests siguientes. `conftest.py` restaura el entorno tras cada test. El fallo estaba latente desde antes; el módulo nuevo lo destapó por orden alfabético.
- 126 tests en verde.

## 0.23.0 - Flujo para añadir ejercicios desde una fuente externa

- Nuevo `docs/roles/prompt-ejercicio-nuevo.md`: prompt versionado para pedir a un agente externo un ejercicio extraído de una transcripción o un artículo, con los vocabularios cerrados y el inventario de material embebidos. Vive en el repositorio para que no se desincronice del catálogo, y `tests/test_prompt_ejercicio.py` falla si alguien amplía un dominio sin actualizarlo.
- Nuevo `scripts/validar_ejercicio.py`: valida de forma **determinista** todo lo comprobable —dominios, material, costes por dimensión, referencias cruzadas, unicidad e id, reglas de descripción de `docs/05`, coherencia de la prescripción— e informa además de qué cubre ya el catálogo en ese patrón, para que «¿aporta algo?» sea una comparación y no una pregunta abierta. Un LLM validando conformidad de esquema es más lento, no determinista y puede equivocarse donde un script no puede.
- **Puerta de seguridad lumbar**: un ejercicio nuevo no entra como `impacto_lumbar: verde` sin `--confirmo-verde`. `impacto_lumbar` y `coste_dimensiones` son entradas directas del motor de decisión y un modelo leyendo un vídeo no conoce los episodios lumbares del atleta; el prompt le prohíbe proponer `verde` y le exige justificar ambos campos.
- **Corregido un valor mal tipado en el catálogo**: YAML 1.1 convierte `no` en el booleano `False`, así que `compatibilidad_bjj: no` se leía como `False` en cuatro ejercicios (los dos swings, el windmill y el russian twist) y en el propio dominio de `valores`. Hoy nadie lee ese campo, así que no había fallo activo, pero una comparación futura del tipo `== "no"` nunca habría casado — y ese valor marca justo los ejercicios que no deben ir antes de BJJ. Los valores van entrecomillados y hay dos tests nuevos que vigilan el tipo y la pertenencia al dominio.
- `docs/roles/README.md` actualizado: decía «como no hay tests ni build» con 109 tests y un build en el repositorio.
- 11 tests nuevos (109 en total, suite en verde).

## 0.22.1 - Roadmap al día

- `docs/10` conservaba los estados de antes de escribir una sola línea de código: la Fase 8 figuraba como «No iniciada» con la aplicación desplegada y en uso, y el «Próximo hito» seguía apuntando a completar las fases 1–6. Las fases 0 a 8 pasan a **cerradas**, cada una con el documento y el módulo que la implementan, y la **Fase 9 (uso personal y calibración) queda en curso desde el 10 de agosto de 2026**.
- El «Próximo hito» pasa a ser calibrar el modelo con uso real, con sus criterios: propuestas rechazadas de forma sistemática, RPE real contra previsto, validación del criterio lumbar por la respuesta posterior y retirada de campos que generan fricción. Se anota que los datos ya se persisten y salen por `GET /api/export`.
- La sección «Puerta de entrada a la aplicación» se marca como superada pero se conserva: su criterio —primero se documenta, después se construye— sigue vigente para cualquier ampliación del modelo.
- `README.md` y `AGENTS.md` sincronizados con ese estado.

## 0.22.0 - Intención del ejercicio y peso usado

- El catálogo no decía nada sobre el peso: «Swing a dos manos 8×9» no indicaba con qué kettlebell. La biblioteca **sigue sin prescribir kilos** —el modelo de carga de `docs/12` es ciego a la intensidad y el perfil no tiene un dato de fuerza por ejercicio— y en su lugar declara **con qué intención** se hace el ejercicio, dejando que el atleta ajuste.
- Nueva sección «Intención del ejercicio» en `docs/05`: la intención se deriva del primer elemento de `objetivos`, que ya existía en los 28 ejercicios, reducido a un vocabulario cerrado (`fuerza`, `potencia`, `resistencia`, `control`, `coordinacion`, `movilidad`, `cardio`, `recuperacion`).
- Junto a la intención se muestra la **reserva de repeticiones de la familia** (tabla de `docs/06`), que es la instrucción concreta para elegir el peso: en familia B, «deja 1-3 repeticiones en recámara». Solo aparece donde significa algo — en dosis por repeticiones, no en isométricos, segundos, saltos ni pasadas, ni en B0/B4, que no buscan estímulo.
- **Peso usado en línea** (`PesoUsado.svelte`) en Ejecución, con las kettlebells del perfil (8/12/16 kg) a un toque. Antes el único acceso al campo era el modal de desviación, que obligaba a marcar el ítem como «modificado»: semánticamente falso cuando lo hiciste tal cual. El backend ya aceptaba `carga_kg_real` con estado `completado`; faltaba la pantalla.
- El peso **no altera la carga calculada**: se acumula para poder sugerir progresión más adelante (`docs/07`), y hay un test que lo fija para que no se cuele una dependencia sin decidirlo.
- 6 tests nuevos (98 en total, suite en verde): intención y reserva en la propuesta, ejercicios sin carga externa, apuntar el peso sin declarar desviación, el peso no cambia los puntos, y la reserva solo donde aplica.

## 0.21.3 - Salidas del cierre

- **Trampa introducida en 0.21.2**: el redirigido a Cierre saltaba cada vez que se tocaba «Hoy», no solo al arrancar, así que una sesión sin cerrar dejaba la aplicación bloqueada en esa pantalla. Ahora el cierre se puede **aplazar** («Ahora no»): la sesión sigue pendiente y se recuerda al volver a abrir, pero se puede seguir usando el resto.
- **Cancelar admite también sesiones `finalizada`**, no solo `en_curso`. Es el caso de darla por hecha por error: esa sesión ya estaba aportando carga a los días siguientes, así que cancelarla se la retira. Es una corrección de registro (criterio 7 de `docs/14`). Desde `cerrada` sigue rechazándose: ahí el cierre pudo congelar la ventana de una dimensión y la corrección se hace por ítem desde el historial.
- Cierre gana dos salidas: «Ahora no» y «Descartar sesión», esta última con confirmación por ser irreversible.
- `docs/14` recoge ambas reglas y deja explícito que **el cierre admite quedarse en lo mínimo**: la sensación es obligatoria y las molestias opcionales.
- 3 tests nuevos y uno sustituido (93 en total, suite en verde): cancelar una finalizada retira su carga, una cerrada ya no se cancela, el cierre acepta ir sin molestias y no se cancela dos veces.

## 0.21.2 - Dos huecos de recuperación del flujo

Al recorrer los casos reales de uso aparecieron dos estados de los que no se podía volver:

- **Sesión finalizada sin cierre**: `GET /api/hoy` solo miraba las sesiones `en_curso`, así que recargar en la pantalla de cierre perdía la respuesta posterior en silencio y sin manera de retomarla — y es la que congela la ventana de una dimensión tras una molestia (`docs/12`, criterio 5). Ahora se devuelve como `sesion_pendiente_cierre` y la aplicación lleva a Cierre al arrancar.
- **Propuesta sin empezar**: se recuperaba en memoria, pero la barra de navegación solo lleva a Hoy, Historial y Perfil, así que era inalcanzable: tras recargar, la única salida era declarar el estado otra vez y descartarla. Estado diario muestra ahora un aviso con acceso a la propuesta y advierte de que redeclarar la descarta.
- 1 test nuevo (90 en total, suite en verde) y corregidos dos tests propios: uno comparaba la respuesta de `/api/hoy` como diccionario exacto, que se rompe al añadir claves, y otro usaba un valor de `sensacion` fuera del literal de `schemas.py`.

## 0.21.1 - Rotación de contraseña

- Nuevo `scripts/cambiar_password.py`. `init_db.py` no toca un usuario existente (no hay registro, docs/14) y termina con éxito diciéndolo, así que era fácil creer que había cambiado la contraseña cuando no. El script nuevo actualiza el hash, **invalida todas las sesiones abiertas** —una contraseña se rota porque la anterior ya no es de fiar, y sus cookies durarían 30 días más— y limpia los intentos fallidos. Exige un mínimo de 12 caracteres.
- `.gitignore`: la BD y **sus copias**. `*.db` no cubría `fitlosophy.db.bak-…`; ahora se ignoran también `*.db.*`, `*.bak`, `*.sqlite` y los ficheros WAL/SHM. La base contiene datos personales de salud, el hash de la contraseña y los tokens de sesión.

## 0.21.0 - Una sola sesión en marcha

- **Causa raíz**: el estado del frontend vivía solo en memoria, así que recargar o reabrir la aplicación a mitad de sesión dejaba en la pantalla de estado diario, donde lo único posible era declararlo otra vez → nueva propuesta → y al aceptar, una **segunda sesión en curso** el mismo día. No era mal uso: era la consecuencia inevitable de recargar.
- Nueva sección «Una sola sesión en marcha» en `docs/14`: como mucho una sesión activa y una propuesta vigente en cada momento; reabrir a mitad de sesión devuelve a esa sesión; redeclarar el estado diario descarta la propuesta anterior en lugar de acumularla; y una sesión se puede cancelar.
- Backend: `POST /api/estado-diario` y `POST /api/sesiones` responden 409 si hay una sesión `en_curso` (con el `sesion_id` en el detalle, para que la interfaz pueda llevar allí). Nuevo estado `cancelada` y endpoint `POST /api/sesiones/{id}/cancelar`. Nueva columna `proposals.estado` (`vigente` | `aceptada` | `descartada`) con migración idempotente que además normaliza las bases de datos existentes.
- Nuevo `GET /api/hoy` con la sesión activa y la propuesta vigente: es lo que permite al frontend repoblar el flujo tras recargar, en lugar de empezar de cero.
- Frontend: al arrancar se recupera el flujo desde `/api/hoy` y no se redirige hasta saber qué hay en marcha (antes se expulsaba de Ejecución a quien recargaba dentro de su sesión). Botón «Cancelar sesión» en Ejecución, con confirmación, porque el invariante nuevo haría que una sesión abierta por error bloqueara el día entero.
- El historial deja de mostrar propuestas descartadas y sesiones canceladas: son ruido de haber redeclarado el estado, no lo que pasó ese día. La carga nunca las contó (`construir_historial` solo lee sesiones finalizadas y cerradas).
- 6 tests nuevos (89 en total, suite en verde): segunda sesión rechazada, redeclarar descarta la anterior, cancelar libera el día, una sesión cancelada no aporta carga ni aparece en el historial, solo se cancela lo que está en curso, y `/api/hoy` refleja lo que hay en marcha.

## 0.20.0 - Ejecución de los ejercicios en el catálogo

- El catálogo era un modelo de decisión y dosificación, sin ningún campo que dijera **cómo** se hace cada ejercicio: la pantalla solo podía mostrar nombre, dosis y justificación. Se notaba sobre todo en la escalera de agilidad, cuya prescripción (`pasadas_por_patron`) se expresaba «por patrón» mientras el catálogo no enumeraba esos patrones en ninguna parte: «4 pasadas» era una dosis que no se podía ejecutar.
- Nueva sección «Ejecución» en `docs/05` con dos campos y sus criterios: `descripcion` (obligatoria, una o dos frases de ejecución con la clave técnica que más importa en este perfil) y `patrones` (obligatoria cuando la dosis se expresa por patrón).
- `data/ejercicios.yaml`: descripción para los **28** ejercicios y los cinco patrones de la escalera de agilidad. Las descripciones de los ejercicios con `impacto_lumbar: rojo` declaran su límite en palabras, no solo con la etiqueta.
- La API resuelve `descripcion` y `patrones` desde el catálogo en cada lectura, sin persistirlos con la propuesta: corregir un texto se refleja también en las sesiones ya guardadas.
- Nuevo `AccionesEjercicio.svelte`: pie de cada ítem con «Cómo se hace» (plegado por defecto) y «Ver vídeo», como dos botones de ancho completo y 44 px de alto. Sustituye a la lupa de 13 px pegada al nombre, que no llegaba al objetivo táctil mínimo y que además convertía el nombre entero en un enlace: tocar el ejercicio sacaba de la aplicación a YouTube sin haberlo pedido. Ahora el nombre es solo texto.
- La explicación de la propuesta pasa a un plegable «Por qué esta sesión» (nuevo `Plegable.svelte`, reutilizable): ocupaba la pantalla completa del móvil antes del primer ejercicio, y es trazabilidad para consultar, no lectura diaria. La cabecera conserva visibles familia, RPE y duración; el plegable añade además las reglas aplicadas.
- Dos iconos nuevos en `Icon.svelte`: `chevron` (gira 90° al desplegar) y `video`.
- `pasadas_por_patron` pasa a respetar la familia como el resto de claves de dosificación. No cambia ninguna dosis actual —este ejercicio solo aparece en B0, que ya fuerza dosis mínima por la regla 8 de `docs/06`— pero deja de ser una excepción a la espera de usarse en otro bloque. La dosis se muestra como «4 pasadas por patrón».
- 8 tests nuevos (83 en total, suite en verde): integridad del catálogo (descripción obligatoria, sin duplicar la dosis, dosis por patrón ↔ patrones enumerados, aviso en palabras de los ejercicios rojos) y la ejecución expuesta en propuesta, sesión e historial.

## 0.19.0 - Caché del frontend y puerto del despliegue

- Los estáticos se sirven con `Cache-Control` explícito (`fitlosophy_api/static.py`). `StaticFiles` solo enviaba `ETag` y `Last-Modified`, así que navegador y CDN cacheaban por heurística: tras recompilar, el túnel seguía sirviendo un `index.html` viejo que apuntaba a los JS/CSS de la compilación anterior y los cambios no llegaban a la URL pública. Ahora `assets/` (nombres con hash de contenido de Vite) va con `immutable` a un año, y todo lo de nombre fijo (`index.html`, `favicon.svg`, `icono-*.png`) con `no-cache, must-revalidate`, que revalida con un 304 sin cuerpo. No hace falta ningún `?v=`: el hash del nombre ya identifica la versión.
- Puerto del servicio: **10012** (antes 8000), en el servicio systemd y en el proxy de desarrollo de Vite. Nuevas claves `FITLOSOPHY_HOST` y `FITLOSOPHY_PORT` en el `.env`, que el servicio systemd lee con `EnvironmentFile`: una sola fuente de configuración.
- El servicio escucha en `0.0.0.0`: el túnel lo gestiona un contenedor de cloudflared configurado desde el panel de Cloudflare (sin `config.yml` local), que llega al host por `172.17.0.1`, y además se accede desde la LAN por `192.168.1.145:10012`. `--forwarded-allow-ips` incluye ahora `172.17.0.0/16`, porque el proxy no llega desde loopback y sin ello uvicorn ignoraba `X-Forwarded-Proto`.
- `FITLOSOPHY_COOKIE_SECURE` pasa a admitir `auto` (nuevo valor por defecto): la cookie se marca `Secure` según el esquema real de la petición, protegida por el túnel y utilizable por HTTP en la LAN, donde una cookie `Secure` se descartaría y el login no funcionaría.
- Nueva `FITLOSOPHY_PROXIES_CONFIABLES`: `CF-Connecting-IP` solo se acepta de loopback y de la red de Docker. Con el puerto abierto en la LAN, sin esto bastaba con ir cambiando esa cabecera a mano para tener intentos de login ilimitados.
- Nuevo `scripts/desplegar.sh`: recompila el frontend, reinicia el servicio, espera a que responda, verifica que la cabecera de caché sigue puesta y purga el caché de Cloudflare si hay `CLOUDFLARE_API_TOKEN` y `CLOUDFLARE_ZONE_ID` en el `.env` (ambas opcionales).
- 8 tests nuevos (75 en total, suite en verde): `index.html` y los ficheros de nombre fijo se revalidan, los de `assets/` son inmutables, la revalidación devuelve 304, la cookie se marca `Secure` solo por HTTPS y la IP declarada por un peer no confiable se ignora.

## 0.18.0 - Configuración por `.env` y freno de fuerza bruta en el login

- Configuración del despliegue en `app/backend/.env` (ignorado por git) con plantilla versionada en `.env.example`. Nuevo `fitlosophy_api/config.py`: lector de `.env` con la librería estándar, sin dependencias nuevas (AGENTS.md). Precedencia entorno > `.env` > valor por defecto, de modo que systemd o una variable puntual siguen ganando; `FITLOSOPHY_ENV_FILE` permite mover el fichero y `tests/conftest.py` lo desactiva para que la suite no dependa de la máquina.
- Protección del login contra fuerza bruta (`auth.py`), que era el punto débil al publicar la app por un túnel: umbral **por IP** (5 fallos en 15 min → bloqueo de 15 min, duplicado por cada tanda acumulada en 24 h hasta 1 h) y umbral **global** (50 fallos en 15 min → login frenado desde cualquier IP, contra el ataque distribuido). Se responde 429 con `Retry-After`; durante el bloqueo se rechaza también la contraseña correcta, un intento rechazado no alarga el castigo y un login correcto limpia los fallos de esa IP. Nueva tabla `login_failures`, purgada a las 48 h; umbrales configurables por `.env`.
- La IP del cliente se toma de `CF-Connecting-IP` (la escribe Cloudflare) y, en su defecto, de `request.client`, que uvicorn reescribe con `--proxy-headers --forwarded-allow-ips`.
- Nuevo `FITLOSOPHY_COOKIE_SECURE`: la cookie de sesión se marca `Secure` en producción sin romper el desarrollo por `http://localhost`. `delete_cookie` pasa a repetir los atributos del `set_cookie` para que el logout la borre de verdad.
- `httpx2` declarado en el extra `dev` de `pyproject.toml`: `starlette.testclient` lo exige y sin él no se podían ejecutar los tests de la API.
- 9 tests nuevos (67 en total, suite en verde): bloqueo por IP, aislamiento entre IPs, limpieza tras acierto, expiración de la ventana, umbral global y cuatro del cargador de `.env`.

## 0.17.0 - Rediseño oscuro del frontend

- Rediseño visual y de usabilidad del MVP según `docs/superpowers/specs/2026-08-03-redisenio-frontend-mvp-design.md`: tema oscuro deportivo con acento lima (tokens en `app.css` con `@theme` de Tailwind 4), Barlow Condensed + Inter autoalojadas (`@fontsource`, únicas dependencias nuevas) e iconos de relleno propios (`Icon.svelte`, sin librería).
- Componentes nuevos: `SliderDolor` (0–10 con gradiente semáforo), `Chips` (material, con Todo/Nada y tatami fijo), `BarraProgreso` («n de m» en Ejecución); `Opciones` pasa a control segmentado oscuro conservando su API.
- Usabilidad móvil: objetivos táctiles ≥ 44 px, recuperación con texto «Bien/Regular/Mal» (los valores de API no cambian), NavBar con iconos y logout reubicado a Perfil.
- Sin cambios funcionales: misma API, mismos payloads, mismos stores y router; el contenido de seguridad (violaciones, incertidumbres, congelación) se conserva destacado. Verificado con capturas de las 7 pantallas y suite del backend intacta (58 tests).
- Identidad del proyecto: marca «mancuerna en diagonal» lima sobre oscuro como `logo.svg`, `icono.svg` + PNGs (180/192/512) y `favicon.svg` en `app/frontend/public/`; la cabecera y el login llevan la marca, e `index.html` enlaza favicon, apple-touch-icon y `theme-color`. La cabecera solo se muestra con sesión iniciada (el login ya no duplica el título) y los ítems del historial muestran la dosis en su propia línea (nada de cortes a mitad de palabra).
- Ayuda de ejercicios: cada nombre de ejercicio en Propuesta y Ejecución enlaza a una búsqueda de vídeo en YouTube (nueva pestaña, icono de lupa), para quien no conoce todavía todos los movimientos.

## 0.16.0 - Corrección completa de registros (criterio 7 de docs/14)

- Nuevo endpoint `PUT /api/sesiones/{id}/items/{item_id}`: corrige el registro de un ítem ya finalizado (estado, ejercicio real, dosis real, motivo). La dosis real corregida sustituye a la prevista — se recalculan los `puntos_reales` del ítem (incluido el ×1.25 por volumen sobre rango de `docs/12`) — y con ellos la carga de los días siguientes (criterio 4). Con la sesión en curso se rechaza (409): ahí se marca con PATCH.
- Lógica compartida entre PATCH (marcado en ejecución) y PUT (corrección posterior): mismo guardado de estado y mismas advertencias de reglas duras en sustituciones.
- Frontend (Historial): corrección por ítem con modal (completado / con cambios / sustituido / no realizado, valores reales y motivo) y corrección del cierre en línea (sensación + molestias); el detalle del día muestra además las dimensiones congeladas por el cierre.
- Tests formales del criterio 7: dosis corregida → carga recalculada desde el historial persistido; dosis sobre rango → puntos ×1.25; cierre corregido sin molestias → dimensión descongelada; PUT rechazado con sesión en curso. 58 tests en total, suite en verde.

## 0.15.0 - Tests E2E del flujo completo

- Dos pruebas funcionales nuevas que cierran la cobertura del criterio 2 de `docs/14` (flujo extremo a extremo) por los caminos que faltaban:
  - `test_flujo_completo_con_bjj_y_sustitucion_en_ejecucion`: BJJ declarado + estado diario → familia A, marcado por las cuatro vías del modal de ejecución (incluida la **sustitución con ejercicio real**, que solo se registraba en la interfaz), validaciones 422 del esquema (sustituido sin `exercise_id_real`, modificado sin valores reales), finalizar con recálculo del sustituto, cierre con congelación lumbar y verificación del historial (física + BJJ, `exercise_id_real` persistido).
  - `test_flujo_sin_material_e2e`: modo sin material (vacaciones/viaje, `docs/14`) de extremo a extremo hasta el historial, con el check por defecto al finalizar.
- Verificados con prueba de mutación: el test del flujo con BJJ detecta la pérdida del `exercise_id_real` en el PATCH de ítems (rojo con mutación, verde al revertir).
- `*.db` añadido a `.gitignore`: la BD SQLite local de desarrollo no se versiona.

## 0.14.0 - Frontend del MVP (Svelte 5 + Tailwind 4)

- Nueva `app/frontend/`: aplicación responsive con las 6 pantallas del MVP (`docs/14`) más login: estado diario (con selector de material disponible), propuesta (con sustitución validada y motivo del rechazo visible), ejecución (check por ítem + modal de desviación), cierre, historial (registro/corrección de BJJ, corrección de RPE) y perfil (JSON editable + exportación).
- Router por hash propio (sin dependencias): en producción basta servir `dist/` con `StaticFiles(html=True)`; en desarrollo, proxy de `/api` a uvicorn (puerto 8000).
- Backend: la API sirve el frontend compilado si existe (`app/frontend/dist`) y expone `GET /api/ejercicios` (catálogo ligero para el selector de sustituciones).
- `package-lock.json` incluido; `node_modules/` y `dist/` ignorados.
- Fix de un test dependiente de la hora del día: `test_bjj_registro_correccion_y_carga` construía el BJJ «hace 20 h», que de 20:00 a 23:59 locales caía en el día actual y no disparaba la regla C4 (el motor usa el día natural anterior, `docs/03`). La fecha ahora se construye ayer a la misma hora + 1 min (edad ≈ 23 h 59 min, ventana ×1.0 de `docs/12`).

## 0.13.0 - API REST del MVP

- Nuevo paquete `fitlosophy_api` (FastAPI + SQLite stdlib): auth de usuario único (pbkdf2, cookie HttpOnly de 30 días), sin registro.
- Flujo completo del MVP como endpoints: estado diario → propuesta (con explicación e incertidumbre) → sustitución validada → sesión con marcado por ítem (completado/modificado/sustituido/no_realizado) → finalizar con RPE real → cierre con congelación de ventana tras molestia.
- Historial (días, detalle propuesta vs realizado), registro y corrección de BJJ, perfil editable, exportación JSON completa.
- El recálculo con dosis real y la congelación de dimensiones se implementaron en el núcleo `fitlosophy` (sin duplicar lógica).
- 12 tests de API nuevos (53 en total): acceso exigido, flujo E2E, rechazo 409 de sustituciones inválidas, congelación, correcciones y export.
- `scripts/init_db.py` y `app/backend/README.md` con instalación y arranque.

## 0.12.0 - Motor ejecutable en Python

- Nueva `app/backend/`: paquete `fitlosophy` (Python 3.11+, pyyaml) con el modelo de carga (`load.py`), el motor de decisión (`engine.py`, reglas D/C/P) y el generador de sesiones (`generator.py`) implementados según `docs/12`, `docs/03` y `docs/06`.
- 41 tests en verde: `test_load.py` (aritmética de `docs/12`) y `test_cases.py` (los 10 casos de `docs/13` como pruebas funcionales ejecutables).
- Correcciones de coherencia detectadas por la implementación: el ejemplo de `docs/12` omitía el agarre del peso muerto (agarre real 8, presupuesto 0 y tirón pendiente; actualizado en `docs/06` y `docs/13`); el sábado del caso 8 queda con agarre baja tras el decaimiento.
- AGENTS.md y README actualizados: el repo pasa a tener código ejecutable con suite de tests.

## 0.11.0 - Material disponible por día

- Nuevo input `material_disponible` en el estado diario (`docs/03`): selector del inventario del garaje con marcar/desmarcar todo; por defecto todo disponible. La lista vacía equivale al modo sin material (vacaciones, viajes); el tatami cuenta siempre como suelo.
- Filtro de material en el generador (`docs/06`, regla 9): solo entran ejercicios con el material requerido disponible; los patrones sin ejercicios posibles se declaran pendientes en la explicación.
- Nuevo flag `sin_material` en el catálogo para ejercicios válidos incluso sin nada: flexiones, pica, puente de glúteos, planchas y dead bug.
- Dos ejercicios nuevos sin material: sentadilla libre y zancada hacia delante (cobertura de `dominante_rodilla`).
- Limitación conocida: sin barra, TRX ni gomas no hay tirón con el catálogo actual; se declara en la explicación.

## 0.10.0 - Diseño del MVP

- Nuevo `docs/14`: definición del MVP (Fase 7) con el contexto de uso real (momento de decisión ~16:15, BJJ declarado a diario, material siempre de garaje).
- Seis pantallas definidas: estado diario, propuesta, ejecución con marcado por ítem (check + modal de modificación), cierre con «Finalizar», historial y perfil.
- Alcance del algoritmo en la primera versión y lista explícita de lo que queda fuera.
- Acceso por usuario y contraseña: aplicación privada de un único usuario.
- Ocho criterios de aceptación funcionales; los casos de `docs/13` se convierten en las pruebas del MVP.

## 0.9.0 - Validación manual con casos de uso

- Nuevo `docs/13`: 10 casos ejecutados a mano con la aritmética completa (familia B potente, familia A con BJJ, dolor lumbar, BJJ incierto, día rojo con motivación, día post-doble-sesión, datos incompletos, semana simulada completa, sustituciones y bisagra en días consecutivos).
- Incoherencias encontradas y corregidas: umbral exacto media/alta y presupuesto crítico (`docs/12`), definición operativa de «bisagra exigente» en D5 (`docs/03`).
- Comportamiento deliberado registrado para calibración: prohibición categórica de agarre medio/alto en familia A (I4).
- Fases 0-6 del roadmap cerradas; la puerta de entrada al desarrollo queda abierta en cuanto al diseño.

## 0.8.0 - Generador de sesiones

- `docs/06` reescrito como generador completo: bloques B0-B4, plantillas por familia A-D y reglas de composición, dosificación, sustitución y validación final contra el presupuesto.
- Reglas nuevas: B0/B4 no computan en el presupuesto; la dosis mínima reduce a la mitad el coste bajo (familias A y C).
- Ejemplo completo coherente con `docs/12`: familia A con lumbar, bisagra y agarre cargadas, validación numérica paso a paso y ejemplo de sustitución rechazada.
- Valores provisionales del generador identificados.

## 0.7.0 - Motor de decisión formal

- `docs/03` reescrito: cuestionario diario mínimo definitivo, reglas duras (D1-D6), de carga (C1-C6) y de preferencia (P1-P3) con orden de prioridad explícito.
- Flujo completo en pseudocódigo: del estado diario a familia de sesión, presupuesto por dimensión y patrones prioritarios/restringidos.
- Matriz de tipos de sesión (semáforo × BJJ × carga total) y formato de explicación esperada para cada decisión.
- Valores provisionales del motor identificados (umbral de dolor, factor de presupuesto compatible, ausencia de patrón).

## 0.6.0 - Ampliación de la biblioteca

- `data/ejercicios.yaml` pasa a `version: 2`: el coste escalar se sustituye por `coste_dimensiones` (mapa dimensión → bajo/medio/alto, según `docs/12`).
- Nuevos metadatos en todos los ejercicios: `nivel`, `lateralidad`, flags `explosivo`/`isometrico` y enlaces de `progresiones`, `regresiones` y `sustitutos`.
- 5 ejercicios nuevos: plancha frontal, dead bug, press militar con kettlebell, flexión en pica y dominada asistida con goma. Los 15 patrones de la taxonomía tienen ahora al menos un ejercicio.
- Nuevos dominios en `valores`: `nivel`, `lateralidad`, `nivel_coste` y `dimensiones`. El antiguo dominio `coste` desaparece.

## 0.5.0 - Modelo de carga e inferencia

- Nuevo `docs/12`: dimensiones de carga definitivas, ventanas y decaimiento, puntuación provisional, ajustes por dosis, carga estimada del BJJ y reglas de acumulación e inferencia.
- Ejemplo completo de cálculo en pseudocódigo (exceso de bisagra y agarre tras swing + peso muerto + BJJ).
- `docs/09` y `docs/04` actualizados para referenciar el modelo; todos los valores numéricos marcados como provisionales (calibración en Fase 9).

## 0.4.0 - Taxonomía de patrones

- Taxonomía cerrada de 15 patrones de movimiento en `docs/05`, con criterios de asignación y dimensiones que alimenta cada patrón.
- Nuevo dominio `patron` en `data/ejercicios.yaml → valores`; todos los ejercicios validados contra él.
- Nuevo campo opcional `secundarios` para patrones secundarios (swing a una mano, windmill, remo unilateral).
- Patrones sin ejercicio identificados para la ampliación de la biblioteca: `core_antiextension`, `empuje_vertical`.

## 0.3.0 - Glosario y modelo de dominio

- Nuevo `docs/11`: glosario con definiciones únicas y modelo de entidades (Fase 1 del roadmap).
- Decisiones de modelado cerradas: propuesta ≠ realizada, ejercicio ≠ variante ≠ dosis, carga multidimensional.
- Valores provisionales identificados (dimensiones de carga, taxonomía de patrones, decaimiento).
- Estado del diseño actualizado en `docs/00`.

## 0.2.0 - Roadmap y fuentes de datos

- Documento agregador `docs/00` con el contexto completo del programa.
- Roadmap del producto (`docs/10`): fases 0–12, criterios de entrada/salida y puerta de entrada a la aplicación.
- Especificación de fuentes de datos e inferencias (`docs/09`): datos declarados, registrados y derivados.
- README alineado con la numeración de fases del roadmap.
- `AGENTS.md` con la guía para agentes y el flujo opcional de dos IAs (`docs/roles/`, `docs/superpowers/`, `opencode.json`).

## 0.1.0 - Inicial

- Estructura base del repositorio.
- Perfil y objetivos iniciales.
- Filosofía del sistema adaptativo.
- Motor de decisión diario.
- Gestión de carga.
- Biblioteca inicial de ejercicios.
- Modelo YAML preparado para una futura aplicación web.
