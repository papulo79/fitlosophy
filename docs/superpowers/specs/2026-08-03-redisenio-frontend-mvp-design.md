# Rediseño visual y de usabilidad del frontend MVP — Spec de diseño

Fecha: 2026-08-03 · Estado: aprobado por el usuario (dirección, iconografía y controles validados con mockups)

## Contexto y objetivo

El frontend del MVP (`app/frontend/`, Svelte 5 + Tailwind 4 + Vite) es funcional pero visualmente deficiente: sin iconos, tipografía por defecto del sistema, paleta gris genérica y controles pequeños. Este rediseño lo convierte en una app móvil-primero con carácter propio, sin tocar flujos, API, stores ni router.

Decisiones ya tomadas con el usuario (mockups en `.superpowers/brainstorm/2415888-1785784549/`):

- **Contexto de uso**: móvil sobre todo (garaje/gimnasio, una mano, lectura rápida entre series).
- **Alcance**: visual + usabilidad. Mismas pantallas y flujo; se puede reordenar/simplificar lo que estorbe. Cero cambios funcionales (la API y los tests del backend no se tocan).
- **Dirección visual**: oscuro deportivo (estilo WHOOP / Nike Training).
- **Iconografía**: relleno sólido, SVG propio sin librería.
- **Estado diario**: deslizador con gradiente para el dolor; el contador de progreso de la variante «pizarra» se incorpora a Ejecución.

## 1. Fundamentos (tokens de diseño)

Definidos en `app/frontend/src/app.css` con `@theme` de Tailwind 4 (sin `tailwind.config.js`).

### Color

| Token | Valor | Uso |
|---|---|---|
| `fondo` | `#10131a` | fondo global |
| `superficie` | `#1a1f2b` | tarjetas, modales, barra de navegación |
| `borde` | `#232a38` | bordes y separadores |
| `texto` | `#e8eaf0` | texto principal |
| `apagado` | `#9aa3b2` | texto secundario |
| `tenue` | `#6b7280` | etiquetas, placeholders |
| `acento` | `#c8f04a` | solo lo accionable: CTA, selección activa, progreso |
| `verde` | `#3ecf6e` | semáforo / éxito sobre oscuro |
| `ambar` | `#e0b34f` | semáforo / advertencias |
| `rojo` | `#e05a4a` | semáforo / errores, no realizado |

El acento lima queda reservado a acciones y estados activos; el semáforo del dominio (recuperación, dolor, impacto lumbar) usa su propia escala para no confundirse con el acento.

### Tipografía

- **Barlow Condensed** 600/700: titulares de pantalla, nombre de familia de sesión y CTAs.
- **Inter** 400/500/600/700: todo lo demás.
- Se autoalojan con `@fontsource/barlow-condensed` y `@fontsource/inter` (devDependencies; las empaqueta Vite). Son las **dos únicas dependencias nuevas**: la app se sirve en local y no puede depender de conectividad (Google Fonts queda descartado).

### Iconos

Componente propio `src/lib/Icon.svelte` con SVG de relleno sólido dibujados a mano (~17): `hoy` (pulso), `historial` (calendario), `perfil` (usuario), `check`, `aviso` (triángulo), `mas` (puntos), `exportar` (descarga), `cerrar` (cruz), `corregir` (lápiz), `atras` (chevron), `plus`, `bjj` (kimono), `logout`, `fisica` (mancuerna), `recuperacion` (corazón), `descanso` (luna), `sin_registro` (círculo punteado). Props: `nombre`, `tam` (px, 20 por defecto). Sin librería de iconos.

## 2. Componentes (`app/frontend/src/lib/`)

- `Icon.svelte` — sprite de relleno descrito arriba.
- `Opciones.svelte` — se reestiliza (misma API de props) como control segmentado grande: opciones ≥ 44 px de alto, seleccionada en acento o en color de semáforo según variante.
- `SliderDolor.svelte` — deslizador 0–10 con gradiente verde→ámbar→rojo, pulgar ≥ 34 px y leyenda «0 · sin dolor / 10 · máximo»; el valor actual se muestra en la etiqueta de la sección (no dentro del pulgar). `bind:valor`.
- `Chips.svelte` — chips on/off (≥ 40 px) para el material disponible, con acciones «Todo / Nada». El tatami es caso especial: siempre fijo (cuenta como suelo), no es un chip seleccionable y «Todo / Nada» no se aplica a él (comportamiento actual, `EstadoDiario.svelte`). Se conserva la semántica actual del envío: con todo el inventario marcado **no se envía** `material_disponible` (equivale a «todo disponible»), no se envía un `null` literal; el componente adapta su estado interno a esa lógica.
- `BarraProgreso.svelte` — «n de m» + barra en acento, para la cabecera de Ejecución.
- Modales *bottom-sheet*: se conserva el patrón existente (fondo oscuro translúcido, hoja redondeada por arriba) reestilizado a superficie oscura.

## 3. Pantallas (mismo flujo, misma API)

Regla general: **se conserva todo el contenido y los datos que cada pantalla muestra y envía hoy; solo cambia la presentación**. Lo que sigue describe los cambios, no una lista exhaustiva de lo que existe.

- **App.svelte**: fondo oscuro global; cabecera mínima con «FITLOSOPHY» en Barlow Condensed; `main` mantiene `max-w-xl` centrado. **NavBar.svelte**: misma composición actual (Hoy / Historial / Perfil) con icono de relleno + etiqueta y activo en acento; el botón «Salir» sale de la barra y pasa a la pantalla de Perfil (con icono `logout`).
- **Login**: tarjeta centrada oscura con titular condensado; inputs oscuros con foco en acento.
- **EstadoDiario**: controles del mockup validado — recuperación como segmentado con semáforo y texto visible «Bien / Regular / Mal» (los valores enviados a la API siguen siendo `verde`/`amarillo`/`rojo`; etiquetas nuevas en `etiquetas.js`); dolor con `SliderDolor` (zona obligatoria si dolor > 0, como hoy); BJJ como segmentado Sí/No/Incierto + segmentado Técnico/Normal/Duro condicional; material con `Chips` (tatami fijo, ver §2); CTA «GENERAR SESIÓN» en acento y Barlow Condensed. **Se conserva la sección plegable de opcionales** (`limitacion`, `sueno`, `tiempo_disponible`, `preferencia`, `circunstancias`) que se envía a la API — solo se reestiliza.
- **Propuesta**: familia en titular condensado grande; ítems agrupados por bloque en tarjetas; explicación e incertidumbres en tarjeta destacada con icono de aviso; sustitución en bottom-sheet (mismo flujo, rechazo 409 con motivo visible); CTA «EMPEZAR SESIÓN». **Se conserva todo lo demás que muestra hoy**: violaciones de reglas con `propuesta.valida` (información de seguridad lumbar, destacada con icono de aviso en rojo/ámbar), dimensiones restringidas, «versión reducida», BJJ efectivo y notas.
- **Ejecución**: cabecera con familia + `BarraProgreso` («n de m», rescate de la variante pizarra); ítems en tarjetas con check de 48 px (pendiente → borde, completado → acento, no realizado → rojo); modal de desviación reestilizado; CTA «FINALIZAR SESIÓN» y selección de RPE con `Opciones`.
- **Cierre**: sensación con `Opciones` (Como estaba previsto / Más duro / Más suave); editor de molestias (zona + intensidad + añadir/quitar con iconos); dimensiones congeladas visibles con icono de aviso.
- **Historial**: lista de días con iconos por tipo (`fisica`, `recuperacion`, `bjj`, `descanso`, `sin_registro`) además de la etiqueta; detalle del día en tarjetas; corrección de RPE/BJJ/cierre con icono de lápiz; corrección de ítem en bottom-sheet (funcionalidad añadida en 0.16.0, se reestiliza).
- **Perfil**: editor JSON con fuente monoespaciada sobre superficie oscura; botón de exportación con icono de descarga; botón «Salir» (logout) con icono, reubicado desde NavBar.

## 4. Usabilidad

- Todos los objetivos táctiles ≥ 44 px; uso a una mano en móvil primero (desktop queda centrado con `max-w-xl`, aceptable).
- Contraste WCAG AA sobre fondo oscuro en todo el texto (texto `#e8eaf0` y apagado `#9aa3b2` sobre `#10131a`/`#1a1f2b` lo cumplen; el tenue `#6b7280` solo para etiquetas en mayúsculas grandes o placeholders).
- Estados vacíos y errores con icono + mensaje; nada de texto gris suelto.
- El acento lima solo en lo accionable: nunca como texto largo ni fondo de contenido.

## 5. Arquitectura y límites

- Sin cambios en `src/lib/api.js`, `src/lib/stores.svelte.js`, router hash de `App.svelte` ni llamadas a la API.
- Sin dependencias nuevas salvo los dos `@fontsource` (devDependencies).
- `etiquetas.js` se conserva (etiquetas de dominio en español); si el rediseño necesita una etiqueta nueva (p. ej. «Bien / Regular / Mal» para recuperación), se añade ahí.
- Texto visible siempre en español (convención del repo).

## 6. Verificación

- `npm run build` en verde tras cada tarea de implementación.
- Capturas de las 7 pantallas (servidor `vite preview` + captura headless con Chromium, p. ej. vía `npx playwright` o `chromium --headless --screenshot`; herramienta **solo de verificación, no pasa a ser dependencia del proyecto**) para revisión visual antes de cerrar.
- Suite del backend (`pytest`) intacta: no hay cambio funcional.

## 7. Fuera de alcance

- Modo claro, PWA/offline, animaciones complejas, rediseño de flujos, pantallas nuevas, cambios de API, modo escritorio dedicado.
