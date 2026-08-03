# Rediseño del frontend MVP (oscuro deportivo) — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reestilizar el frontend MVP de Fitlosophy (7 pantallas + shell) con la dirección «oscuro deportivo» validada con el usuario: tokens oscuros con acento lima, Barlow Condensed + Inter autoalojadas, iconos de relleno propios, controles táctiles grandes (slider de dolor, chips de material, barra de progreso en Ejecución).

**Architecture:** Todo el cambio es presentacional: tokens en `app.css` (`@theme` de Tailwind 4), 5 componentes nuevos/reestilizados en `src/lib/` (`Icon`, `Opciones`, `SliderDolor`, `Chips`, `BarraProgreso`) y reescritura de las plantillas de las rutas conservando los `<script>` (salvo imports). No se tocan `api.js`, `stores.svelte.js`, el router ni la API del backend.

**Tech Stack:** Svelte 5 (runes), Tailwind 4 (`@tailwindcss/vite`, sin config JS), Vite 6, `@fontsource/inter` + `@fontsource/barlow-condensed` (las dos únicas dependencias nuevas, devDependencies empaquetadas por Vite).

**Spec:** `docs/superpowers/specs/2026-08-03-redisenio-frontend-mvp-design.md`

**Nota sobre verificación:** no hay framework de tests de frontend y el spec prohíbe dependencias nuevas más allá de las fuentes. La verificación de cada tarea es `npm run build` en verde; la verificación visual global es la Tarea 15 (capturas). Trabajar en la rama `feat/redisenio-frontend` y commitear tras cada tarea.

**Convenciones de diseño (valen para todas las tareas):**

- Tokens disponibles como utilidades Tailwind: `bg-fondo`, `bg-superficie`, `border-borde`, `text-texto`, `text-apagado`, `text-tenue`, `bg-acento`/`text-acento`/`border-acento`, `text-verde`/`bg-verde`, `text-ambar`/`bg-ambar`, `text-rojo`/`bg-rojo`, `font-display` (Barlow Condensed), `font-sans` (Inter).
- El acento lima solo en lo accionable (CTA, selección activa, progreso). Texto sobre `bg-acento` siempre `text-fondo`.
- Objetivos táctiles ≥ 44 px. Errores con icono `aviso` + texto `text-rojo` sobre fondo `bg-rojo/10`.
- Los `<script>` de las rutas se conservan; solo se añaden imports de componentes nuevos donde se indique.

---

### Task 0: Rama y fuentes autoalojadas

**Files:**
- Modify: `app/frontend/package.json` (vía npm install)

- [ ] **Step 1: Crear la rama**

```bash
cd /home/reverendo/Desarrollo/fitlosophy
git checkout -b feat/redisenio-frontend
```

- [ ] **Step 2: Instalar las fuentes (devDependencies)**

```bash
cd app/frontend
npm install -D @fontsource/inter@^5 @fontsource/barlow-condensed@^5
```

Expected: `package.json` incluye ambos paquetes en `devDependencies`; `package-lock.json` actualizado.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/package.json app/frontend/package-lock.json
git commit -m "chore: add self-hosted fonts (Inter, Barlow Condensed)"
```

---

### Task 1: Tokens de diseño en app.css

**Files:**
- Modify: `app/frontend/src/app.css` (reemplazo completo)

- [ ] **Step 1: Reescribir `app/frontend/src/app.css`**

```css
@import "tailwindcss";
@import "@fontsource/inter/400.css";
@import "@fontsource/inter/500.css";
@import "@fontsource/inter/600.css";
@import "@fontsource/inter/700.css";
@import "@fontsource/barlow-condensed/600.css";
@import "@fontsource/barlow-condensed/700.css";

@theme {
  /* Rediseño oscuro deportivo (spec docs/superpowers/specs/2026-08-03-…-design.md) */
  --color-fondo: #10131a;
  --color-superficie: #1a1f2b;
  --color-borde: #232a38;
  --color-texto: #e8eaf0;
  --color-apagado: #9aa3b2;
  --color-tenue: #6b7280;
  --color-acento: #c8f04a;
  --color-verde: #3ecf6e;
  --color-ambar: #e0b34f;
  --color-rojo: #e05a4a;
  --font-sans: "Inter", system-ui, sans-serif;
  --font-display: "Barlow Condensed", "Inter", system-ui, sans-serif;
}

body {
  @apply bg-fondo font-sans text-texto antialiased;
}

/* Inputs heredan el esquema oscuro. */
input,
select,
textarea {
  color-scheme: dark;
}
```

- [ ] **Step 2: Verificar build**

Run: `cd app/frontend && npm run build`
Expected: build OK. La pantalla se verá rota mezclando tokens nuevos con clases viejas; se arregla en las tareas siguientes.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/app.css
git commit -m "feat: dark design tokens in app.css"
```

---

### Task 2: Componente Icon.svelte (sprite de relleno propio)

**Files:**
- Create: `app/frontend/src/lib/Icon.svelte`

- [ ] **Step 1: Crear el componente**

```svelte
<script>
  /** Iconos de relleno sólido propios (spec §1). Uso: <Icon nombre="check" tam={20} /> */
  const TRAZOS = {
    hoy: "M14 3h-4l-2 8H3v2h6.6l2.4 8 4-12H21v-2h-6.6z",
    historial: "M7 2a1 1 0 0 1 1 1v1h8V3a1 1 0 1 1 2 0v1h1a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h1V3a1 1 0 0 1 1-1zm12 8H5v9h14z",
    perfil: "M12 3a5 5 0 1 1 0 10 5 5 0 0 1 0-10zm0 12c4 0 7.5 1.8 8.5 5.5a1 1 0 0 1-1 .5h-15a1 1 0 0 1-1-.5C4.5 16.8 8 15 12 15z",
    check: "M9.55 17.3 4.8 12.55l1.4-1.4 3.35 3.35 8.25-8.25 1.4 1.4z",
    aviso: "M12 3 1.5 21h21zm-1 7h2v4.5h-2zm0 6h2v2h-2z",
    mas: "M5 9.8a2.2 2.2 0 1 1 0 4.4 2.2 2.2 0 0 1 0-4.4m7 0a2.2 2.2 0 1 1 0 4.4 2.2 2.2 0 0 1 0-4.4m7 0a2.2 2.2 0 1 1 0 4.4 2.2 2.2 0 0 1 0-4.4",
    exportar: "M12 3a1 1 0 0 1 1 1v8.6l2.8-2.8a1 1 0 1 1 1.4 1.4l-4.5 4.5a1 1 0 0 1-1.4 0l-4.5-4.5a1 1 0 1 1 1.4-1.4l2.8 2.8V4a1 1 0 0 1 1-1zM5 18h14a1 1 0 1 1 0 2H5a1 1 0 1 1 0-2z",
    cerrar: "M6.4 5 5 6.4 10.6 12 5 17.6 6.4 19 12 13.4 17.6 19l1.4-1.4L13.4 12 19 6.4 17.6 5 12 10.6z",
    corregir: "M3 17.2V21h3.8L17.9 9.9l-3.8-3.8zM20.7 7.1a1 1 0 0 0 0-1.4l-2.4-2.4a1 1 0 0 0-1.4 0l-1.8 1.8 3.8 3.8z",
    atras: "M14.5 5 7.5 12l7 7 1.4-1.4-5.6-5.6 5.6-5.6z",
    plus: "M11 5h2v6h6v2h-6v6h-2v-6H5v-2h6z",
    bjj: "M12 2 8 4l-4.5 3L5 9.5l2-1V21h10V8.5l2 1 1.5-2.5L16 4zm-1 4.5 1-1.7 1 1.7-1 1.5zM9 10.5l3 4 3-4 1.2 1L13 16v4h-2v-4l-3.2-4.5z",
    logout: "M4 5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2h-2V5H6v14h6v-2h2v2a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zm12.5 4.5L21 14l-4.5 4.5-1.4-1.4 2.1-2.1H9v-2h8.2l-2.1-2.1z",
    fisica: "M3 9a1.5 1.5 0 0 1 3 0v6a1.5 1.5 0 0 1-3 0zm4-2a1.5 1.5 0 0 1 3 0v10a1.5 1.5 0 0 1-3 0zm7 0a1.5 1.5 0 0 1 3 0v10a1.5 1.5 0 0 1-3 0zm4 2a1.5 1.5 0 0 1 3 0v6a1.5 1.5 0 0 1-3 0zM10 11h4v2h-4z",
    recuperacion: "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09A6.06 6.06 0 0 1 16.5 3C19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z",
    descanso: "M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8",
    sin_registro: "M12 4a8 8 0 1 0 8 8h-2a6 6 0 1 1-6-6z",
  };
  let { nombre, tam = 20 } = $props();
</script>

<svg width={tam} height={tam} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" class="shrink-0">
  <path d={TRAZOS[nombre] || TRAZOS.aviso} />
</svg>
```

- [ ] **Step 2: Verificar build** (el componente aún no se usa; el build valida la sintaxis)

Run: `cd app/frontend && npm run build`
Expected: build OK.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/lib/Icon.svelte
git commit -m "feat: add solid-fill Icon component"
```

---

### Task 3: Shell — App.svelte y NavBar.svelte

**Files:**
- Modify: `app/frontend/src/App.svelte` (cabecera y main)
- Modify: `app/frontend/src/lib/NavBar.svelte` (reescritura)

- [ ] **Step 1: App.svelte — reemplazar el bloque de plantilla final**

El `<script>` no cambia. Reemplazar todo lo que hay tras `</script>` por:

```svelte
{#if !session.verificado}
  <p class="p-6 text-center text-apagado">Cargando…</p>
{:else}
  <header class="border-b border-borde bg-superficie">
    <div class="mx-auto max-w-xl px-4 py-3">
      <h1 class="font-display text-2xl font-bold tracking-wide text-acento">FITLOSOPHY</h1>
    </div>
  </header>
  <main class="mx-auto max-w-xl p-4 pb-24">
    {#key base + (parametro || "")}
      <Componente {parametro} />
    {/key}
  </main>
  {#if session.usuario}
    <NavBar />
  {/if}
{/if}
```

- [ ] **Step 2: NavBar.svelte — reescritura completa**

El logout sale de la barra (va a Perfil, Tarea 14). La barra conserva los tres destinos actuales con icono + etiqueta y activo en acento. Como el router es por hash propio, el activo se deriva de `location.hash` con un listener:

```svelte
<script>
  import Icon from "./Icon.svelte";

  const DESTINOS = [
    { ruta: "/estado", icono: "hoy", etiqueta: "Hoy" },
    { ruta: "/historial", icono: "historial", etiqueta: "Historial" },
    { ruta: "/perfil", icono: "perfil", etiqueta: "Perfil" },
  ];

  let hash = $state(location.hash);
  $effect(() => {
    const alCambiar = () => (hash = location.hash);
    window.addEventListener("hashchange", alCambiar);
    return () => window.removeEventListener("hashchange", alCambiar);
  });
  let activo = $derived("/" + (hash.replace(/^#/, "").split("/")[1] || "estado"));
</script>

<nav class="fixed inset-x-0 bottom-0 z-10 border-t border-borde bg-superficie">
  <div class="mx-auto flex max-w-xl">
    {#each DESTINOS as d}
      <a
        href="#{d.ruta}"
        class="flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-semibold {activo === d.ruta ? 'text-acento' : 'text-tenue'}"
      >
        <Icon nombre={d.icono} tam={22} />
        {d.etiqueta}
      </a>
    {/each}
  </div>
</nav>
```

Nota: el `pb-20` del main pasa a `pb-24` para que la barra (ahora más alta) no tape contenido.

- [ ] **Step 3: Verificar build**

Run: `cd app/frontend && npm run build`
Expected: build OK. Las rutas siguen con clases viejas (se verán mal sobre el fondo oscuro); se corrigen en sus tareas.

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/App.svelte app/frontend/src/lib/NavBar.svelte
git commit -m "feat: dark shell with icon navbar"
```

---

### Task 4: Opciones.svelte — control segmentado oscuro

**Files:**
- Modify: `app/frontend/src/lib/Opciones.svelte` (reescritura, misma API de props)

- [ ] **Step 1: Reescribir el componente**

La API se conserva (`opciones`, `bind:valor`, `colores`); los valores de `colores` ahora son clases del tema oscuro. Alto ≥ 44 px.

```svelte
<script>
  /** Grupo de botones grandes para elegir un valor de dominio (segmentado oscuro). */
  let { opciones, valor = $bindable(), colores = {} } = $props();
</script>

<div class="flex gap-2">
  {#each opciones as op}
    <button
      type="button"
      onclick={() => (valor = op.valor)}
      class="min-h-11 flex-1 rounded-xl border px-2 py-3 text-sm font-semibold transition-colors {valor === op.valor
        ? colores[op.valor] || 'border-acento bg-acento text-fondo'
        : 'border-borde bg-superficie text-apagado'}"
    >
      {op.etiqueta}
    </button>
  {/each}
</div>
```

- [ ] **Step 2: Verificar build**

Run: `cd app/frontend && npm run build`
Expected: build OK. Los usos actuales de `Opciones` (recuperación de EstadoDiario, RPE, sensación, BJJ) tomarán el estilo por defecto (seleccionado en acento); el mapa de colores de la recuperación se actualiza en la Tarea 9 junto con la plantilla.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/lib/Opciones.svelte
git commit -m "feat: restyle Opciones as dark segmented control"
```

---

### Task 5: SliderDolor.svelte — deslizador 0–10 con gradiente

**Files:**
- Create: `app/frontend/src/lib/SliderDolor.svelte`

- [ ] **Step 1: Crear el componente**

Input range nativo estilizado (accesible y funcional en móvil sin librerías): pista con gradiente semáforo y pulgar grande con el valor. `bind:valor` (número).

```svelte
<script>
  /** Deslizador de dolor 0–10 con gradiente semáforo (spec §2). bind:valor */
  let { valor = $bindable(0) } = $props();
</script>

<div>
  <input
    bind:value={valor}
    type="range"
    min="0"
    max="10"
    step="1"
    aria-label="Dolor de 0 a 10"
    class="slider-dolor w-full"
  />
  <div class="mt-1 flex justify-between text-xs text-tenue">
    <span>0 · sin dolor</span>
    <span>10 · máximo</span>
  </div>
</div>

<style>
  .slider-dolor {
    -webkit-appearance: none;
    appearance: none;
    height: 26px;
    border-radius: 13px;
    background:
      linear-gradient(#10131a, #10131a) padding-box,
      linear-gradient(90deg, #3ecf6e 0%, #e0b34f 55%, #e05a4a 100%) border-box;
    border: 6px solid transparent;
    outline: none;
  }
  .slider-dolor::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: #e8eaf0;
    border: none;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
    cursor: pointer;
  }
  .slider-dolor::-moz-range-thumb {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: #e8eaf0;
    border: none;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
    cursor: pointer;
  }
</style>
```

El valor se muestra ya en la etiqueta de la sección de EstadoDiario (Tarea 9); el pulgar de 34 px cumple el objetivo táctil.

- [ ] **Step 2: Verificar build**

Run: `cd app/frontend && npm run build`
Expected: build OK.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/lib/SliderDolor.svelte
git commit -m "feat: add pain slider component"
```

---

### Task 6: Chips.svelte — chips on/off para material

**Files:**
- Create: `app/frontend/src/lib/Chips.svelte`

- [ ] **Step 1: Crear el componente**

Estado interno por referencia a un mapa `marcados` (token → bool) propiedad del padre: se conserva la semántica actual del envío («todo marcado = no se envía `material_disponible`») en la pantalla, no aquí. El tatami no entra: la pantalla lo renderiza aparte como chip fijo.

```svelte
<script>
  import Icon from "./Icon.svelte";

  /** Chips on/off ≥ 40 px (spec §2).
   *  `tokens`: lista de tokens seleccionables; `marcados`: mapa token → bool (bindable);
   *  `etiquetas`: mapa token → etiqueta visible. */
  let { tokens, marcados = $bindable({}), etiquetas = {} } = $props();

  function marcarTodo(v) {
    marcados = Object.fromEntries(tokens.map((t) => [t, v]));
  }
</script>

<div>
  <div class="mb-2 flex gap-3 text-xs font-semibold">
    <button type="button" onclick={() => marcarTodo(true)} class="text-acento">Todo</button>
    <button type="button" onclick={() => marcarTodo(false)} class="text-apagado">Nada</button>
  </div>
  <div class="flex flex-wrap gap-2">
    {#each tokens as token}
      <button
        type="button"
        onclick={() => (marcados = { ...marcados, [token]: !marcados[token] })}
        class="flex min-h-10 items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold transition-colors {marcados[token]
          ? 'bg-acento text-fondo'
          : 'bg-superficie text-apagado border border-borde'}"
      >
        {#if marcados[token]}<Icon nombre="check" tam={14} />{/if}
        {etiquetas[token] || token}
      </button>
    {/each}
  </div>
</div>
```

- [ ] **Step 2: Verificar build**

Run: `cd app/frontend && npm run build`
Expected: build OK.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/lib/Chips.svelte
git commit -m "feat: add Chips component for material selection"
```

---

### Task 7: BarraProgreso.svelte — «n de m» + barra

**Files:**
- Create: `app/frontend/src/lib/BarraProgreso.svelte`

- [ ] **Step 1: Crear el componente**

```svelte
<script>
  /** «n de m» + barra de progreso en acento (spec §2). */
  let { hechos = 0, total = 0 } = $props();
  let pct = $derived(total > 0 ? Math.round((hechos / total) * 100) : 0);
</script>

<div class="flex items-center gap-3">
  <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-borde">
    <div class="h-full rounded-full bg-acento transition-all" style="width: {pct}%"></div>
  </div>
  <span class="text-sm text-apagado"><b class="text-texto">{hechos}</b> de {total}</span>
</div>
```

- [ ] **Step 2: Verificar build**

Run: `cd app/frontend && npm run build`
Expected: build OK.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/lib/BarraProgreso.svelte
git commit -m "feat: add session progress bar component"
```

---

### Task 8: Login

**Files:**
- Modify: `app/frontend/src/routes/Login.svelte` (solo plantilla)

- [ ] **Step 1: Reemplazar la plantilla** (el `<script>` no cambia)

```svelte
<div class="mx-auto mt-16 max-w-sm">
  <h2 class="mb-6 text-center font-display text-3xl font-bold tracking-wide text-acento">FITLOSOPHY</h2>
  <form onsubmit={entrar} class="space-y-4">
    <input
      bind:value={username}
      type="text"
      placeholder="Usuario"
      autocomplete="username"
      required
      class="w-full rounded-xl border border-borde bg-superficie px-4 py-3 text-texto placeholder:text-tenue focus:border-acento focus:outline-none"
    />
    <input
      bind:value={password}
      type="password"
      placeholder="Contraseña"
      autocomplete="current-password"
      required
      class="w-full rounded-xl border border-borde bg-superficie px-4 py-3 text-texto placeholder:text-tenue focus:border-acento focus:outline-none"
    />
    {#if error}
      <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
        <Icon nombre="aviso" tam={16} /> {error}
      </p>
    {/if}
    <button
      type="submit"
      disabled={cargando}
      class="w-full rounded-xl bg-acento py-3 font-display text-lg font-bold tracking-wide text-fondo disabled:opacity-50"
    >
      {cargando ? "ENTRANDO…" : "ENTRAR"}
    </button>
  </form>
</div>
```

Y en el `<script>` añadir el import:

```js
import Icon from "../lib/Icon.svelte";
```

- [ ] **Step 2: Verificar build**

Run: `cd app/frontend && npm run build`
Expected: build OK.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/routes/Login.svelte
git commit -m "feat: restyle login screen"
```

---

### Task 9: EstadoDiario — controles nuevos, mismo payload

**Files:**
- Modify: `app/frontend/src/routes/EstadoDiario.svelte` (imports + plantilla; la función `enviar` y el estado no cambian)
- Modify: `app/frontend/src/lib/etiquetas.js` (etiquetas de recuperación)

- [ ] **Step 1: Añadir etiquetas de recuperación a `etiquetas.js`**

Al final del archivo:

```js
/** Recuperación: texto visible; los valores de API siguen siendo verde/amarillo/rojo. */
export const RECUPERACION = {
  verde: "Bien",
  amarillo: "Regular",
  rojo: "Mal",
};
```

- [ ] **Step 2: EstadoDiario.svelte — imports**

Añadir los imports que falten (el de `Opciones` ya existe):

```js
import SliderDolor from "../lib/SliderDolor.svelte";
import Chips from "../lib/Chips.svelte";
import Icon from "../lib/Icon.svelte";
import { RECUPERACION } from "../lib/etiquetas.js";
```

El `<script>` conserva todo lo demás (estado, `$effect` de perfil, `materialVariable`, `todoMarcado`, `enviar`) exactamente igual.

- [ ] **Step 3: Reemplazar la plantilla**

```svelte
<h2 class="mb-4 font-display text-2xl font-bold tracking-wide">¿CÓMO ESTÁS HOY?</h2>

<form onsubmit={enviar} class="space-y-6">
  <section>
    <p class="mb-2 text-xs font-semibold uppercase tracking-wider text-tenue">Recuperación</p>
    <Opciones
      bind:valor={recuperacion}
      opciones={[
        { valor: "verde", etiqueta: RECUPERACION.verde },
        { valor: "amarillo", etiqueta: RECUPERACION.amarillo },
        { valor: "rojo", etiqueta: RECUPERACION.rojo },
      ]}
      colores={{
        verde: "border-verde bg-verde text-fondo",
        amarillo: "border-ambar bg-ambar text-fondo",
        rojo: "border-rojo bg-rojo text-texto",
      }}
    />
  </section>

  <section>
    <p class="mb-2 text-xs font-semibold uppercase tracking-wider text-tenue">
      Dolor · <span class="text-base font-bold normal-case text-texto">{dolor}</span>
    </p>
    <SliderDolor bind:valor={dolor} />
    {#if dolor > 0}
      <input
        bind:value={zonaDolor}
        type="text"
        placeholder="Zona del dolor (obligatorio)"
        class="mt-3 w-full rounded-xl border border-borde bg-superficie px-4 py-3 text-texto placeholder:text-tenue focus:border-acento focus:outline-none"
      />
    {/if}
  </section>

  <section>
    <p class="mb-2 text-xs font-semibold uppercase tracking-wider text-tenue">¿Hay BJJ hoy?</p>
    <Opciones
      bind:valor={bjj}
      opciones={[
        { valor: "si", etiqueta: "Sí" },
        { valor: "no", etiqueta: "No" },
        { valor: "incierto", etiqueta: "Incierto" },
      ]}
    />
    {#if bjj === "si"}
      <p class="mt-3 mb-2 text-xs font-semibold uppercase tracking-wider text-tenue">Tipo de sesión de BJJ</p>
      <Opciones
        bind:valor={tipoBjj}
        opciones={[
          { valor: "tecnico", etiqueta: "Técnico" },
          { valor: "normal", etiqueta: "Normal" },
          { valor: "duro", etiqueta: "Duro" },
        ]}
      />
    {/if}
  </section>

  {#if materialVariable.length > 0}
    <section>
      <p class="mb-2 text-xs font-semibold uppercase tracking-wider text-tenue">Material disponible hoy</p>
      <Chips tokens={materialVariable} bind:marcados etiquetas={ETIQUETAS_MATERIAL} />
      <p class="mt-2 flex items-center gap-1.5 text-xs text-tenue">
        <Icon nombre="check" tam={12} /> Tatami siempre disponible (cuenta como suelo)
      </p>
    </section>
  {/if}

  <section>
    <button type="button" onclick={() => (mostrarOpcionales = !mostrarOpcionales)} class="flex items-center gap-1.5 text-sm font-medium text-acento">
      <Icon nombre={mostrarOpcionales ? "cerrar" : "plus"} tam={14} />
      {mostrarOpcionales ? "Ocultar opcionales" : "Limitación, sueño, tiempo, preferencias…"}
    </button>
    {#if mostrarOpcionales}
      <div class="mt-3 space-y-3">
        <input bind:value={limitacion} type="text" placeholder="Limitación puntual (ej. hombro cargado)" class="w-full rounded-xl border border-borde bg-superficie px-4 py-3 text-texto placeholder:text-tenue focus:border-acento focus:outline-none" />
        <input bind:value={sueno} type="text" placeholder="Sueño (ej. 6 h, mal)" class="w-full rounded-xl border border-borde bg-superficie px-4 py-3 text-texto placeholder:text-tenue focus:border-acento focus:outline-none" />
        <input bind:value={tiempo} type="number" min="1" placeholder="Tiempo disponible (minutos)" class="w-full rounded-xl border border-borde bg-superficie px-4 py-3 text-texto placeholder:text-tenue focus:border-acento focus:outline-none" />
        <input bind:value={preferencia} type="text" placeholder="Preferencia (ej. sin impacto)" class="w-full rounded-xl border border-borde bg-superficie px-4 py-3 text-texto placeholder:text-tenue focus:border-acento focus:outline-none" />
        <input bind:value={circunstancias} type="text" placeholder="Circunstancias (ej. viaje, calor)" class="w-full rounded-xl border border-borde bg-superficie px-4 py-3 text-texto placeholder:text-tenue focus:border-acento focus:outline-none" />
      </div>
    {/if}
  </section>

  {#if error}
    <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
      <Icon nombre="aviso" tam={16} /> {error}
    </p>
  {/if}

  <button type="submit" disabled={cargando} class="w-full rounded-xl bg-acento py-4 font-display text-xl font-bold tracking-wider text-fondo disabled:opacity-50">
    {cargando ? "DECIDIENDO…" : "GENERAR SESIÓN"}
  </button>
</form>
```

Nota: el tatami fijo pasa del checkbox deshabilitado a una línea informativa (sigue sin ser seleccionable y `materialVariable` lo excluye como antes). El payload de `enviar` no cambia en absoluto.

- [ ] **Step 4: Verificar build**

Run: `cd app/frontend && npm run build`
Expected: build OK.

- [ ] **Step 5: Commit**

```bash
git add app/frontend/src/routes/EstadoDiario.svelte app/frontend/src/lib/etiquetas.js
git commit -m "feat: restyle daily state screen with slider and chips"
```

---

### Task 10: Propuesta

**Files:**
- Modify: `app/frontend/src/routes/Propuesta.svelte` (imports + plantilla; el `<script>` de sustitución/empezar no cambia)

- [ ] **Step 1: Añadir import**

```js
import Icon from "../lib/Icon.svelte";
```

- [ ] **Step 2: Reemplazar la plantilla**

Se conserva TODO el contenido actual (RPE/duración/reducida/BJJ, explicación, incertidumbres, violaciones, restringidas, notas, sustitución con 409).

```svelte
{#if propuesta}
  <div class="space-y-5">
    <header class="rounded-xl border border-borde bg-superficie p-4">
      <p class="font-display text-2xl font-bold tracking-wide text-acento">{FAMILIAS[propuesta.familia] || `Familia ${propuesta.familia}`}</p>
      <p class="mt-1 text-sm text-apagado">
        RPE previsto {propuesta.rpe_previsto} · ~{propuesta.duracion_estimada_min} min
        {#if propuesta.reducida}· <span class="font-semibold text-ambar">versión reducida</span>{/if}
        {#if propuesta.bjj_efectivo && propuesta.bjj_efectivo !== "no"}· BJJ {propuesta.bjj_efectivo}{/if}
      </p>
      <p class="mt-2 text-sm text-texto">{propuesta.explicacion}</p>
    </header>

    {#if propuesta.incertidumbres?.length}
      <div class="rounded-xl border border-ambar/40 bg-ambar/10 p-4">
        <p class="flex items-center gap-2 text-sm font-semibold text-ambar">
          <Icon nombre="aviso" tam={16} /> Incertidumbre (el motor lo asume y lo declara):
        </p>
        <ul class="mt-1 list-disc pl-5 text-sm text-ambar">
          {#each propuesta.incertidumbres as inc}
            <li>{inc}</li>
          {/each}
        </ul>
      </div>
    {/if}

    {#if !propuesta.valida}
      <div class="rounded-xl border border-rojo/40 bg-rojo/10 p-4 text-sm text-rojo">
        <p class="flex items-center gap-2 font-semibold">
          <Icon nombre="aviso" tam={16} /> La sesión no cumple alguna regla:
        </p>
        <ul class="mt-1 list-disc pl-5">
          {#each propuesta.violaciones as v}
            <li>{v}</li>
          {/each}
        </ul>
      </div>
    {/if}

    {#if propuesta.carga?.restringidas?.length}
      <p class="text-sm text-apagado">
        Dimensiones restringidas hoy: <span class="font-semibold text-texto">{propuesta.carga.restringidas.join(", ")}</span>
      </p>
    {/if}

    {#each grupos as grupo}
      <section>
        <h3 class="mb-2 text-xs font-bold uppercase tracking-wider text-tenue">{BLOQUES[grupo.bloque] || grupo.bloque}</h3>
        <div class="space-y-2">
          {#each grupo.items as item}
            {@const idx = propuesta.items.indexOf(item)}
            <div class="flex items-start justify-between gap-2 rounded-xl border border-borde bg-superficie p-4">
              <div>
                <p class="font-semibold text-texto">{item.nombre}</p>
                <p class="text-sm text-apagado">{item.dosis}</p>
                {#if item.justificacion}
                  <p class="mt-1 text-xs text-tenue">{item.justificacion}</p>
                {/if}
              </div>
              <button onclick={() => abrirSustitucion(idx)} class="flex min-h-11 shrink-0 items-center gap-1.5 rounded-lg border border-borde px-3 py-2 text-sm font-semibold text-apagado">
                <Icon nombre="corregir" tam={14} /> Cambiar
              </button>
            </div>
          {/each}
        </div>
      </section>
    {/each}

    {#if propuesta.notas?.length}
      <ul class="list-disc pl-5 text-sm text-apagado">
        {#each propuesta.notas as nota}
          <li>{nota}</li>
        {/each}
      </ul>
    {/if}

    {#if error}
      <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
        <Icon nombre="aviso" tam={16} /> {error}
      </p>
    {/if}

    <button onclick={empezar} disabled={cargando} class="w-full rounded-xl bg-acento py-4 font-display text-xl font-bold tracking-wider text-fondo disabled:opacity-50">
      {cargando ? "CREANDO…" : "EMPEZAR SESIÓN"}
    </button>
  </div>

  {#if modalIndice !== null}
    <div class="fixed inset-0 z-20 flex items-end justify-center bg-black/60" role="dialog">
      <div class="max-h-[80vh] w-full max-w-xl overflow-y-auto rounded-t-2xl bg-superficie p-5">
        <h3 class="mb-3 text-lg font-bold text-texto">Sustituir «{propuesta.items[modalIndice].nombre}»</h3>
        <select bind:value={candidato} class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto focus:border-acento focus:outline-none">
          <option value="" disabled>Elige un ejercicio…</option>
          {#each catalogo as ej}
            <option value={ej.id}>{ej.nombre}</option>
          {/each}
        </select>

        {#if motivos.length}
          <div class="mt-3 rounded-lg border border-ambar/40 bg-ambar/10 p-3 text-sm text-ambar">
            <p class="flex items-center gap-2 font-semibold"><Icon nombre="aviso" tam={16} /> Sustitución rechazada:</p>
            <ul class="mt-1 list-disc pl-5">
              {#each motivos as m}
                <li>{m}</li>
              {/each}
            </ul>
          </div>
        {/if}
        {#if errorModal}
          <p class="mt-3 flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
            <Icon nombre="aviso" tam={16} /> {errorModal}
          </p>
        {/if}

        <div class="mt-4 flex gap-2">
          <button onclick={() => (modalIndice = null)} class="flex-1 rounded-xl border border-borde py-3 font-medium text-apagado">Cancelar</button>
          <button onclick={sustituir} disabled={!candidato} class="flex-1 rounded-xl bg-acento py-3 font-semibold text-fondo disabled:opacity-50">
            Sustituir
          </button>
        </div>
      </div>
    </div>
  {/if}
{/if}
```

- [ ] **Step 3: Verificar build**

Run: `cd app/frontend && npm run build`
Expected: build OK.

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/routes/Propuesta.svelte
git commit -m "feat: restyle proposal screen"
```

---

### Task 11: Ejecución — barra de progreso y tarjetas oscuras

**Files:**
- Modify: `app/frontend/src/routes/Ejecucion.svelte` (imports + plantilla; el `<script>` no cambia)

- [ ] **Step 1: Añadir imports y derivados de progreso**

En el `<script>`, tras los imports existentes:

```js
import Icon from "../lib/Icon.svelte";
import BarraProgreso from "../lib/BarraProgreso.svelte";
```

Y tras `let grupos = ...`:

```js
let hechos = $derived((sesion?.items || []).filter((i) => i.estado !== "pendiente").length);
let total = $derived((sesion?.items || []).length);
```

- [ ] **Step 2: Reemplazar la plantilla**

```svelte
{#if sesion}
  <div class="space-y-5">
    <header>
      <h2 class="font-display text-2xl font-bold tracking-wide text-acento">{FAMILIAS[sesion.familia] || `Familia ${sesion.familia}`}</h2>
      <p class="mt-0.5 mb-2 text-sm text-apagado">Marca cada ejercicio al completarlo. Usa los puntos solo si te desvías de lo previsto.</p>
      <BarraProgreso {hechos} {total} />
    </header>

    {#if advertencias.length}
      <div class="rounded-xl border border-ambar/40 bg-ambar/10 p-3 text-sm text-ambar">
        <p class="flex items-center gap-2 font-semibold"><Icon nombre="aviso" tam={16} /> Advertencias (se registra igualmente):</p>
        <ul class="mt-1 list-disc pl-5">
          {#each advertencias as a}
            <li>{a}</li>
          {/each}
        </ul>
      </div>
    {/if}

    {#each grupos as grupo}
      <section>
        <h3 class="mb-2 text-xs font-bold uppercase tracking-wider text-tenue">{BLOQUES[grupo.bloque] || grupo.bloque}</h3>
        <div class="space-y-2">
          {#each grupo.items as item}
            <div class="flex items-center gap-3 rounded-xl border border-borde bg-superficie p-3 {item.estado !== 'pendiente' ? 'opacity-60' : ''}">
              <button
                onclick={() => marcar(item)}
                aria-label="Completado"
                class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border-2 {item.estado === 'pendiente'
                  ? 'border-borde text-transparent'
                  : item.estado === 'no_realizado'
                    ? 'border-rojo bg-rojo/15 text-rojo'
                    : 'border-acento bg-acento text-fondo'}"
              >
                <Icon nombre={item.estado === "no_realizado" ? "cerrar" : "check"} tam={22} />
              </button>
              <div class="min-w-0 flex-1">
                <p class="font-semibold text-texto">{item.nombre}</p>
                <p class="text-sm text-apagado">{item.dosis}</p>
                {#if item.estado !== "pendiente"}
                  <p class="text-xs text-tenue">
                    {ESTADOS_ITEM[item.estado]}{item.motivo ? ` · ${item.motivo}` : ""}
                  </p>
                {/if}
              </div>
              {#if sesion.estado === "en_curso"}
                <button onclick={() => abrirModal(item)} aria-label="Opciones" class="flex min-h-11 shrink-0 items-center rounded-lg border border-borde px-3 py-2 text-apagado">
                  <Icon nombre="mas" tam={18} />
                </button>
              {/if}
            </div>
          {/each}
        </div>
      </section>
    {/each}

    {#if error}
      <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
        <Icon nombre="aviso" tam={16} /> {error}
      </p>
    {/if}

    {#if sesion.estado === "en_curso"}
      {#if finalizando}
        <div class="rounded-xl border border-borde bg-superficie p-4">
          <p class="mb-2 text-xs font-semibold uppercase tracking-wider text-tenue">RPE real de la sesión (1-10)</p>
          <Opciones bind:valor={rpe} opciones={[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => ({ valor: n, etiqueta: String(n) }))} />
          <div class="mt-4 flex gap-2">
            <button onclick={() => (finalizando = false)} class="flex-1 rounded-xl border border-borde py-3 font-medium text-apagado">Aún no</button>
            <button onclick={finalizar} disabled={cargando} class="flex-1 rounded-xl bg-acento py-3 font-semibold text-fondo disabled:opacity-50">
              {cargando ? "Guardando…" : "Finalizar"}
            </button>
          </div>
        </div>
      {:else}
        <button onclick={() => (finalizando = true)} class="w-full rounded-xl bg-acento py-4 font-display text-xl font-bold tracking-wider text-fondo">
          FINALIZAR SESIÓN
        </button>
      {/if}
    {/if}
  </div>

  {#if itemModal}
    <div class="fixed inset-0 z-20 flex items-end justify-center bg-black/60" role="dialog">
      <div class="max-h-[85vh] w-full max-w-xl overflow-y-auto rounded-t-2xl bg-superficie p-5">
        <h3 class="text-lg font-bold text-texto">{itemModal.nombre}</h3>
        <p class="mb-3 text-sm text-apagado">{itemModal.dosis}</p>

        <div class="mb-4 flex gap-2">
          {#each [
              ["modificado", "Completado con cambios"],
              ["sustituido", "Sustituido"],
              ["no_realizado", "No realizado"],
            ] as [valor, etiqueta]}
            <button
              onclick={() => (modo = valor)}
              class="min-h-11 flex-1 rounded-lg border px-2 py-2 text-xs font-semibold {modo === valor
                ? 'border-acento bg-acento text-fondo'
                : 'border-borde bg-fondo text-apagado'}"
            >
              {etiqueta}
            </button>
          {/each}
        </div>

        <div class="space-y-3">
          {#if modo === "sustituido"}
            <select bind:value={formulario.exercise_id} class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto focus:border-acento focus:outline-none">
              <option value="" disabled>Ejercicio realizado…</option>
              {#each catalogo as ej}
                <option value={ej.id}>{ej.nombre}</option>
              {/each}
            </select>
          {/if}
          {#if modo !== "no_realizado"}
            <div class="grid grid-cols-2 gap-2">
              <input bind:value={formulario.series} type="number" min="1" placeholder="Series" class="rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
              <input bind:value={formulario.repeticiones} type="number" min="1" placeholder="Repeticiones" class="rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
              <input bind:value={formulario.segundos} type="number" min="1" placeholder="Segundos" class="rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
              <input bind:value={formulario.minutos} type="number" min="1" placeholder="Minutos" class="rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
              <input bind:value={formulario.carga_kg} type="number" min="0" step="0.5" placeholder="Carga (kg)" class="col-span-2 rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
            </div>
          {/if}
          <input bind:value={formulario.motivo} type="text" placeholder="Motivo (opcional)" class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
        </div>

        {#if errorModal}
          <p class="mt-3 flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
            <Icon nombre="aviso" tam={16} /> {errorModal}
          </p>
        {/if}

        <div class="mt-4 flex gap-2">
          <button onclick={() => (itemModal = null)} class="flex-1 rounded-xl border border-borde py-3 font-medium text-apagado">Cancelar</button>
          <button onclick={guardarDesviacion} class="flex-1 rounded-xl bg-acento py-3 font-semibold text-fondo">Guardar</button>
        </div>
      </div>
    </div>
  {/if}
{/if}
```

- [ ] **Step 3: Verificar build**

Run: `cd app/frontend && npm run build`
Expected: build OK.

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/routes/Ejecucion.svelte
git commit -m "feat: restyle execution screen with progress bar"
```

---

### Task 12: Cierre

**Files:**
- Modify: `app/frontend/src/routes/Cierre.svelte` (imports + plantilla; el `<script>` no cambia)

- [ ] **Step 1: Añadir import**

```js
import Icon from "../lib/Icon.svelte";
```

- [ ] **Step 2: Reemplazar la plantilla**

```svelte
{#if sesion}
  {#if resultado}
    <div class="space-y-5">
      <h2 class="font-display text-2xl font-bold tracking-wide">SESIÓN CERRADA</h2>
      {#if resultado.dimensiones_congeladas?.length}
        <div class="rounded-xl border border-ambar/40 bg-ambar/10 p-4 text-sm text-ambar">
          <p class="flex items-center gap-2 font-semibold">
            <Icon nombre="aviso" tam={16} /> Ventanas congeladas por molestias (la dimensión no estará disponible unos días):
          </p>
          <p class="mt-1">{resultado.dimensiones_congeladas.join(", ")}</p>
        </div>
      {:else}
        <p class="rounded-xl border border-borde bg-superficie p-4 text-sm text-apagado">Sin dimensiones congeladas.</p>
      {/if}
      {#if resultado.zonas_sin_mapear?.length}
        <p class="rounded-xl border border-borde bg-superficie p-4 text-sm text-apagado">
          {resultado.nota} Zonas: {resultado.zonas_sin_mapear.join(", ")}.
        </p>
      {/if}
      <div class="flex gap-2">
        <a href="#/historial" class="flex-1 rounded-xl border border-borde py-3 text-center font-medium text-apagado">Ver historial</a>
        <button onclick={nuevoDia} class="flex-1 rounded-xl bg-acento py-3 font-display text-lg font-bold tracking-wide text-fondo">NUEVO DÍA</button>
      </div>
    </div>
  {:else}
    <div class="space-y-6">
      <h2 class="font-display text-2xl font-bold tracking-wide">CIERRE DE LA SESIÓN</h2>

      <section>
        <p class="mb-2 text-xs font-semibold uppercase tracking-wider text-tenue">¿Cómo ha ido respecto a lo previsto?</p>
        <Opciones
          bind:valor={sensacion}
          opciones={[
            { valor: "como_previsto", etiqueta: "Como estaba previsto" },
            { valor: "mas_duro", etiqueta: "Más duro" },
            { valor: "mas_suave", etiqueta: "Más suave" },
          ]}
        />
      </section>

      <section>
        <p class="mb-2 text-xs font-semibold uppercase tracking-wider text-tenue">Molestias posteriores</p>
        {#each molestias as m, i}
          <div class="mb-2 flex items-center gap-2">
            <input bind:value={m.zona} type="text" placeholder="Zona (ej. lumbar)" class="min-w-0 flex-1 rounded-xl border border-borde bg-superficie px-3 py-3 text-texto placeholder:text-tenue" />
            <input bind:value={m.intensidad} type="number" min="0" max="10" class="w-20 rounded-xl border border-borde bg-superficie px-3 py-3 text-texto" />
            <button onclick={() => quitarMolestia(i)} aria-label="Quitar" class="flex min-h-11 items-center rounded-lg border border-borde px-3 py-3 text-apagado">
              <Icon nombre="cerrar" tam={16} />
            </button>
          </div>
        {/each}
        <button onclick={anadirMolestia} class="flex items-center gap-1.5 text-sm font-medium text-acento">
          <Icon nombre="plus" tam={14} /> Añadir molestia
        </button>
      </section>

      {#if error}
        <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
          <Icon nombre="aviso" tam={16} /> {error}
        </p>
      {/if}

      <button onclick={enviar} disabled={cargando} class="w-full rounded-xl bg-acento py-4 font-display text-xl font-bold tracking-wider text-fondo disabled:opacity-50">
        {cargando ? "GUARDANDO…" : "GUARDAR CIERRE"}
      </button>
    </div>
  {/if}
{/if}
```

- [ ] **Step 3: Verificar build**

Run: `cd app/frontend && npm run build`
Expected: build OK.

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/routes/Cierre.svelte
git commit -m "feat: restyle closure screen"
```

---

### Task 13: Historial

**Files:**
- Modify: `app/frontend/src/routes/Historial.svelte` (imports + plantilla; el `<script>` de datos/correcciones no cambia)

- [ ] **Step 1: Añadir imports y mapa de iconos por tipo de día**

```js
import Icon from "../lib/Icon.svelte";
```

Y tras el mapa `TIPOS_DIA`:

```js
const ICONOS_DIA = {
  fisica: "fisica",
  recuperacion: "recuperacion",
  bjj: "bjj",
  descanso: "descanso",
  sin_registro: "sin_registro",
};
```

- [ ] **Step 2: Reemplazar la plantilla**

```svelte
{#if !parametro}
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="font-display text-2xl font-bold tracking-wide">HISTORIAL (30 DÍAS)</h2>
      <button onclick={() => abrirFormBjj()} class="flex min-h-11 items-center gap-1.5 rounded-xl border border-borde bg-superficie px-3 py-2 text-sm font-semibold text-apagado">
        <Icon nombre="plus" tam={14} /> BJJ
      </button>
    </div>

    {#if errorLista}
      <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
        <Icon nombre="aviso" tam={16} /> {errorLista}
      </p>
    {/if}

    <div class="space-y-2">
      {#each dias as dia}
        <a href="#/historial/{dia.fecha}" class="block rounded-xl border border-borde bg-superficie p-4">
          <div class="flex items-center justify-between">
            <p class="font-semibold text-texto">{dia.fecha}</p>
            <div class="flex gap-2">
              {#each dia.tipos as tipo}
                <span class="flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium {tipo === 'sin_registro'
                    ? 'bg-fondo text-tenue'
                    : tipo === 'descanso'
                      ? 'bg-fondo text-apagado'
                      : 'bg-acento/15 text-acento'}">
                  <Icon nombre={ICONOS_DIA[tipo] || "sin_registro"} tam={14} />
                  {TIPOS_DIA[tipo] || tipo}
                </span>
              {/each}
            </div>
          </div>
          {#if dia.sesiones.length || dia.bjj.length}
            <p class="mt-1 text-sm text-apagado">
              {#each dia.sesiones as s, i}{i > 0 ? " · " : ""}Sesión {s.familia} ({ESTADOS_SESION[s.estado] || s.estado}){/each}
              {#if dia.sesiones.length && dia.bjj.length} · {/if}
              {#each dia.bjj as b, i}{i > 0 ? " · " : ""}BJJ {b.clasificacion} {b.duracion_minutos} min{/each}
            </p>
          {/if}
        </a>
      {/each}
    </div>
  </div>
{:else}
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <h2 class="font-display text-2xl font-bold tracking-wide">{parametro}</h2>
      <div class="flex gap-2">
        <button onclick={() => abrirFormBjj()} class="flex min-h-11 items-center gap-1.5 rounded-xl border border-borde bg-superficie px-3 py-2 text-sm font-semibold text-apagado">
          <Icon nombre="plus" tam={14} /> BJJ
        </button>
        <a href="#/historial" class="flex min-h-11 items-center gap-1.5 rounded-xl border border-borde bg-superficie px-3 py-2 text-sm font-semibold text-apagado">
          <Icon nombre="atras" tam={14} /> Volver
        </a>
      </div>
    </div>

    {#if errorDetalle}
      <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
        <Icon nombre="aviso" tam={16} /> {errorDetalle}
      </p>
    {/if}

    {#if detalle}
      {#if detalle.estados_diarios.length}
        <section class="rounded-xl border border-borde bg-superficie p-4 text-sm text-texto">
          <h3 class="mb-1 font-bold">Estado diario</h3>
          {#each detalle.estados_diarios as e}
            <p class="text-apagado">
              Recuperación {e.recuperacion} · dolor {e.dolor}{e.zona_dolor ? ` (${e.zona_dolor})` : ""} · BJJ: {e.bjj_disponible}{e.tipo_bjj ? ` ${e.tipo_bjj}` : ""}
              {#if e.limitacion}· limitación: {e.limitacion}{/if}
            </p>
          {/each}
        </section>
      {/if}

      {#each detalle.sesiones as s}
        <section class="rounded-xl border border-borde bg-superficie p-4">
          <div class="flex items-center justify-between">
            <h3 class="font-bold text-texto">{FAMILIAS[s.familia] || `Sesión ${s.familia}`}</h3>
            <span class="text-sm text-tenue">{ESTADOS_SESION[s.estado] || s.estado}</span>
          </div>
          <div class="mt-1 flex items-center gap-2 text-sm text-apagado">
            <span>RPE real: {s.rpe_real ?? "—"}</span>
            {#if editandoRpe === s.id}
              <input bind:value={rpeNuevo} type="number" min="1" max="10" class="w-16 rounded-lg border border-borde bg-fondo px-2 py-1 text-texto" />
              <button onclick={() => guardarRpe(s.id)} class="text-sm font-medium text-acento">Guardar</button>
              <button onclick={() => (editandoRpe = null)} class="text-sm text-tenue">Cancelar</button>
            {:else}
              <button onclick={() => { editandoRpe = s.id; rpeNuevo = s.rpe_real || 7; }} class="flex items-center gap-1 text-sm font-medium text-acento">
                <Icon nombre="corregir" tam={13} /> Corregir
              </button>
            {/if}
          </div>
          {#each agruparPorBloque(s.items) as grupo}
            <p class="mt-3 text-xs font-bold uppercase tracking-wider text-tenue">{BLOQUES[grupo.bloque] || grupo.bloque}</p>
            <ul class="mt-1 space-y-1 text-sm">
              {#each grupo.items as item}
                <li class="flex justify-between gap-2">
                  <span class="text-texto">{item.nombre} — <span class="text-apagado">{item.dosis}</span></span>
                  <span class="shrink-0 text-tenue">
                    {ESTADOS_ITEM[item.estado] || item.estado}
                    {#if s.estado !== "en_curso"}
                      <button onclick={() => abrirCorreccionItem(s.id, item)} class="ml-2 font-medium text-acento">Corregir</button>
                    {/if}
                  </span>
                </li>
              {/each}
            </ul>
          {/each}
          {#if s.cierre}
            <div class="mt-3 text-sm text-apagado">
              <p>
                Cierre: {s.cierre.sensacion.replace("_", " ")}
                {#if s.cierre.molestias?.length}· molestias: {s.cierre.molestias.map((m) => `${m.zona} (${m.intensidad})`).join(", ")}{/if}
                {#if s.cierre.dimensiones_congeladas?.length}· congela: {s.cierre.dimensiones_congeladas.join(", ")}{/if}
                <button onclick={() => abrirCorreccionCierre(s)} class="ml-2 inline-flex items-center gap-1 font-medium text-acento">
                  <Icon nombre="corregir" tam={13} /> Corregir
                </button>
              </p>
              {#if cierreCorrigiendo === s.id}
                <div class="mt-2 space-y-3 rounded-xl border border-borde bg-fondo p-3">
                  <Opciones
                    bind:valor={cierreForm.sensacion}
                    opciones={[
                      { valor: "como_previsto", etiqueta: "Como estaba previsto" },
                      { valor: "mas_duro", etiqueta: "Más duro" },
                      { valor: "mas_suave", etiqueta: "Más suave" },
                    ]}
                  />
                  {#each cierreForm.molestias as m, i}
                    <div class="flex gap-2">
                      <input bind:value={m.zona} type="text" placeholder="Zona (ej. lumbar)" class="flex-1 rounded-xl border border-borde bg-superficie px-3 py-2 text-texto placeholder:text-tenue" />
                      <input bind:value={m.intensidad} type="number" min="0" max="10" title="Intensidad 0-10" class="w-20 rounded-xl border border-borde bg-superficie px-3 py-2 text-texto" />
                      <button onclick={() => (cierreForm.molestias = cierreForm.molestias.filter((_, j) => j !== i))} aria-label="Quitar molestia" class="px-2 text-tenue">
                        <Icon nombre="cerrar" tam={14} />
                      </button>
                    </div>
                  {/each}
                  <button onclick={() => (cierreForm.molestias = [...cierreForm.molestias, { zona: "", intensidad: 3 }])} class="flex items-center gap-1.5 text-sm font-medium text-acento">
                    <Icon nombre="plus" tam={13} /> Añadir molestia
                  </button>
                  {#if errorCierre}
                    <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
                      <Icon nombre="aviso" tam={16} /> {errorCierre}
                    </p>
                  {/if}
                  <div class="flex gap-2">
                    <button onclick={() => (cierreCorrigiendo = null)} class="flex-1 rounded-xl border border-borde py-2 font-medium text-apagado">Cancelar</button>
                    <button onclick={guardarCorreccionCierre} class="flex-1 rounded-xl bg-acento py-2 font-semibold text-fondo">Guardar</button>
                  </div>
                </div>
              {/if}
            </div>
          {/if}
        </section>
      {/each}

      {#each detalle.propuestas as p}
        {#if !detalle.sesiones.some((s) => s.proposal_id === p.id)}
          <section class="rounded-xl border border-borde bg-superficie p-4 text-sm">
            <h3 class="font-bold text-texto">Propuesta no ejecutada ({FAMILIAS[p.familia] || p.familia})</h3>
            <p class="mt-1 text-apagado">{p.explicacion}</p>
          </section>
        {/if}
      {/each}

      {#each detalle.bjj as b}
        <section class="rounded-xl border border-borde bg-superficie p-4 text-sm">
          <div class="flex items-center justify-between">
            <h3 class="flex items-center gap-2 font-bold text-texto">
              <Icon nombre="bjj" tam={16} /> BJJ {b.clasificacion} · {b.duracion_minutos} min{b.estimado ? " (estimado)" : ""}
            </h3>
            <button onclick={() => abrirFormBjj(b)} class="flex items-center gap-1 text-sm font-medium text-acento">
              <Icon nombre="corregir" tam={13} /> Corregir
            </button>
          </div>
          <p class="mt-1 text-apagado">
            {#if b.fatiga_agarre}Fatiga de agarre · {/if}{#if b.intensidad_percibida}intensidad {b.intensidad_percibida}/10 · {/if}{b.notas || ""}
          </p>
        </section>
      {/each}

      {#if !detalle.estados_diarios.length && !detalle.sesiones.length && !detalle.bjj.length}
        <p class="text-sm text-tenue">Sin registros este día.</p>
      {/if}
    {:else if !errorDetalle}
      <p class="text-sm text-tenue">Cargando…</p>
    {/if}
  </div>
{/if}

{#if itemCorrigiendo}
  <div class="fixed inset-0 z-20 flex items-end justify-center bg-black/60" role="dialog">
    <div class="max-h-[85vh] w-full max-w-xl overflow-y-auto rounded-t-2xl bg-superficie p-5">
      <h3 class="text-lg font-bold text-texto">Corregir: {itemCorrigiendo.item.nombre}</h3>
      <p class="mb-3 text-sm text-apagado">{itemCorrigiendo.item.dosis} · el cambio recalcula la carga de los días siguientes</p>

      <div class="mb-4 grid grid-cols-2 gap-2">
        {#each [
            ["completado", "Completado tal cual"],
            ["modificado", "Completado con cambios"],
            ["sustituido", "Sustituido"],
            ["no_realizado", "No realizado"],
          ] as [valor, etiqueta]}
          <button
            onclick={() => (modoItem = valor)}
            class="min-h-11 rounded-lg border px-2 py-2 text-xs font-semibold {modoItem === valor
              ? 'border-acento bg-acento text-fondo'
              : 'border-borde bg-fondo text-apagado'}"
          >
            {etiqueta}
          </button>
        {/each}
      </div>

      <div class="space-y-3">
        {#if modoItem === "sustituido"}
          <select bind:value={formItem.exercise_id} class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto focus:border-acento focus:outline-none">
            <option value="" disabled>Ejercicio realizado…</option>
            {#each catalogo as ej}
              <option value={ej.id}>{ej.nombre}</option>
            {/each}
          </select>
        {/if}
        {#if modoItem === "modificado" || modoItem === "sustituido"}
          <div class="grid grid-cols-2 gap-2">
            <input bind:value={formItem.series} type="number" min="1" placeholder="Series" class="rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
            <input bind:value={formItem.repeticiones} type="number" min="1" placeholder="Repeticiones" class="rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
            <input bind:value={formItem.segundos} type="number" min="1" placeholder="Segundos" class="rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
            <input bind:value={formItem.minutos} type="number" min="1" placeholder="Minutos" class="rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
            <input bind:value={formItem.carga_kg} type="number" min="0" step="0.5" placeholder="Carga (kg)" class="col-span-2 rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
          </div>
        {/if}
        <input bind:value={formItem.motivo} type="text" placeholder="Motivo (opcional)" class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
      </div>

      {#if errorItem}
        <p class="mt-3 flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
          <Icon nombre="aviso" tam={16} /> {errorItem}
        </p>
      {/if}

      <div class="mt-4 flex gap-2">
        <button onclick={() => (itemCorrigiendo = null)} class="flex-1 rounded-xl border border-borde py-3 font-medium text-apagado">Cancelar</button>
        <button onclick={guardarCorreccionItem} class="flex-1 rounded-xl bg-acento py-3 font-semibold text-fondo">Guardar</button>
      </div>
    </div>
  </div>
{/if}

{#if mostrarFormBjj}
  <div class="fixed inset-0 z-20 flex items-end justify-center bg-black/60" role="dialog">
    <div class="max-h-[85vh] w-full max-w-xl overflow-y-auto rounded-t-2xl bg-superficie p-5">
      <h3 class="mb-3 text-lg font-bold text-texto">{editandoBjj ? "Corregir registro de BJJ" : "Registrar BJJ"}</h3>
      <div class="space-y-3">
        <div>
          <p class="mb-1 text-xs font-semibold uppercase tracking-wider text-tenue">Clasificación</p>
          <Opciones
            bind:valor={bjj.clasificacion}
            opciones={[
              { valor: "tecnico", etiqueta: "Técnico" },
              { valor: "normal", etiqueta: "Normal" },
              { valor: "duro", etiqueta: "Duro" },
            ]}
          />
        </div>
        <input bind:value={bjj.duracion} type="number" min="1" placeholder="Duración (minutos)" class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
        <input bind:value={bjj.fecha} type="date" class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto" />
        <label class="flex items-center gap-2 text-sm text-texto">
          <input type="checkbox" bind:checked={bjj.fatiga_agarre} class="h-5 w-5 accent-[#c8f04a]" />
          Fatiga de agarre
        </label>
        <input bind:value={bjj.intensidad} type="number" min="1" max="10" placeholder="Intensidad percibida (1-10, opcional)" class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
        <input bind:value={bjj.notas} type="text" placeholder="Notas (opcional)" class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
      </div>
      {#if errorBjj}
        <p class="mt-3 flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
          <Icon nombre="aviso" tam={16} /> {errorBjj}
        </p>
      {/if}
      <div class="mt-4 flex gap-2">
        <button onclick={() => (mostrarFormBjj = false)} class="flex-1 rounded-xl border border-borde py-3 font-medium text-apagado">Cancelar</button>
        <button onclick={guardarBjj} class="flex-1 rounded-xl bg-acento py-3 font-semibold text-fondo">Guardar</button>
      </div>
    </div>
  </div>
{/if}
```

- [ ] **Step 3: Verificar build**

Run: `cd app/frontend && npm run build`
Expected: build OK.

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/routes/Historial.svelte
git commit -m "feat: restyle history screens with day-type icons"
```

---

### Task 14: Perfil + logout reubicado

**Files:**
- Modify: `app/frontend/src/routes/Perfil.svelte` (imports, lógica de logout y plantilla)

- [ ] **Step 1: Añadir imports y función de logout**

En el `<script>`:

```js
import Icon from "../lib/Icon.svelte";
import { session, reiniciarFlujo } from "../lib/stores.svelte.js";

async function salir() {
  await api.post("/api/auth/logout").catch(() => {});
  session.usuario = null;
  reiniciarFlujo();
  location.hash = "#/login";
}
```

- [ ] **Step 2: Reemplazar la plantilla**

```svelte
<div class="space-y-4">
  <h2 class="font-display text-2xl font-bold tracking-wide">PERFIL</h2>
  <p class="text-sm text-apagado">
    Copia editable del perfil (misma forma que <code>data/perfil.yaml</code>). El motor la usa en cada decisión.
    {#if updatedAt}<span class="block text-xs text-tenue">Última actualización: {updatedAt}</span>{/if}
  </p>

  <textarea bind:value={texto} rows="20" spellcheck="false" class="w-full rounded-xl border border-borde bg-superficie p-3 font-mono text-xs text-texto"></textarea>

  {#if error}
    <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
      <Icon nombre="aviso" tam={16} /> {error}
    </p>
  {/if}
  {#if mensaje}
    <p class="flex items-center gap-2 rounded-lg bg-verde/10 p-3 text-sm text-verde">
      <Icon nombre="check" tam={16} /> {mensaje}
    </p>
  {/if}

  <button onclick={guardar} disabled={cargando} class="w-full rounded-xl bg-acento py-3 font-semibold text-fondo disabled:opacity-50">
    {cargando ? "Guardando…" : "Guardar perfil"}
  </button>

  <a href="/api/export" download="fitlosophy-export.json" class="flex items-center justify-center gap-2 rounded-xl border border-borde bg-superficie py-3 font-medium text-apagado">
    <Icon nombre="exportar" tam={16} /> Descargar copia de todos los datos (JSON)
  </a>

  <button onclick={salir} class="flex w-full items-center justify-center gap-2 rounded-xl border border-rojo/40 py-3 font-medium text-rojo">
    <Icon nombre="logout" tam={16} /> Salir
  </button>
</div>
```

- [ ] **Step 3: Verificar build**

Run: `cd app/frontend && npm run build`
Expected: build OK.

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/routes/Perfil.svelte
git commit -m "feat: restyle profile screen and relocate logout"
```

---

### Task 15: Verificación visual y cierre

**Files:**
- Modify: `CHANGELOG.md` (nueva entrada al inicio)

- [ ] **Step 1: Build final y suite del backend**

```bash
cd app/frontend && npm run build
cd ../backend && python3 -m pytest -q
```

Expected: build OK; 58 tests en verde (sin cambios funcionales que los afecten).

- [ ] **Step 2: Capturas de las 7 pantallas**

Arrancar backend de prueba y frontend dev (el dev server proxifica `/api`; `vite preview` no):

```bash
cd app/backend
FITLOSOPHY_DB=/tmp/fitlosophy-shots.db FITLOSOPHY_USER=atleta FITLOSOPHY_PASSWORD=secreto123 python3 scripts/init_db.py
FITLOSOPHY_DB=/tmp/fitlosophy-shots.db PYTHONPATH=src uvicorn "fitlosophy_api.app:create_app" --factory --port 8000 &
cd ../frontend && npm run dev &
```

Nota: `init_db.py` lee la ruta de la BD solo de `FITLOSOPHY_DB` (no acepta argumento posicional) y uvicorn necesita `PYTHONPATH=src` salvo que el paquete esté instalado con `pip install -e ".[dev]"` (ver `app/backend/README.md`).

Capturar con Playwright (herramienta de verificación, NO dependencia del proyecto — no se añade a `package.json`): un script temporal en `/tmp/shots.mjs` que haga login, recorra `#/estado` (con el formulario rellenado), `#/propuesta`, `#/ejecucion`, `#/cierre`, `#/historial` y `#/perfil`, y guarde PNGs (viewport móvil, 390×844) en `.superpowers/screenshots/`. Si Playwright no puede instalarse en el entorno, fallback: pedir al usuario revisión manual en `http://localhost:5173`.

Inspeccionar las capturas con la herramienta de lectura de imágenes y corregir lo que desentone (contraste, desbordes, iconos mal dibujados) antes de seguir.

- [ ] **Step 3: Entrada de CHANGELOG**

Al inicio de `CHANGELOG.md`:

```markdown
## 0.17.0 - Rediseño oscuro del frontend

- Rediseño visual y de usabilidad del MVP según `docs/superpowers/specs/2026-08-03-redisenio-frontend-mvp-design.md`: tema oscuro deportivo con acento lima (tokens en `app.css` con `@theme` de Tailwind 4), Barlow Condensed + Inter autoalojadas (`@fontsource`, únicas dependencias nuevas) e iconos de relleno propios (`Icon.svelte`, sin librería).
- Componentes nuevos: `SliderDolor` (0–10 con gradiente semáforo), `Chips` (material, con Todo/Nada y tatami fijo), `BarraProgreso` («n de m» en Ejecución); `Opciones` pasa a control segmentado oscuro conservando su API.
- Usabilidad móvil: objetivos táctiles ≥ 44 px, recuperación con texto «Bien/Regular/Mal» (los valores de API no cambian), NavBar con iconos y logout reubicado a Perfil.
- Sin cambios funcionales: misma API, mismos payloads, mismos stores y router; el contenido de seguridad (violaciones, incertidumbres, congelación) se conserva destacado.
```

- [ ] **Step 4: Commit final**

```bash
git add -A app/frontend CHANGELOG.md
git commit -m "docs: changelog for frontend redesign"
```

- [ ] **Step 5: Push y merge** (solo si el usuario lo pide; recordar que en el flujo de dos IAs el merge lo hace el revisor)

---

## Resumen de archivos

**Creados:**
- `app/frontend/src/lib/Icon.svelte`
- `app/frontend/src/lib/SliderDolor.svelte`
- `app/frontend/src/lib/Chips.svelte`
- `app/frontend/src/lib/BarraProgreso.svelte`

**Modificados:**
- `app/frontend/package.json` + `package-lock.json` (2 devDependencies)
- `app/frontend/src/app.css`
- `app/frontend/src/App.svelte`
- `app/frontend/src/lib/NavBar.svelte`
- `app/frontend/src/lib/Opciones.svelte`
- `app/frontend/src/lib/etiquetas.js`
- `app/frontend/src/routes/Login.svelte`
- `app/frontend/src/routes/EstadoDiario.svelte`
- `app/frontend/src/routes/Propuesta.svelte`
- `app/frontend/src/routes/Ejecucion.svelte`
- `app/frontend/src/routes/Cierre.svelte`
- `app/frontend/src/routes/Historial.svelte`
- `app/frontend/src/routes/Perfil.svelte`
- `CHANGELOG.md`

**No tocados:** `src/lib/api.js`, `src/lib/stores.svelte.js`, `app/frontend/src/main.js`, `index.html`, todo `app/backend/`.
