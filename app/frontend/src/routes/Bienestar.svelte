<script>
  /** Estado diario (docs/morning_state): registro matutino de bienestar.
   *  Independiente del entrenamiento: un registro por fecha, indicadores
   *  opcionales (parciales), edición de días anteriores y tendencias de
   *  7/14/30 días calculadas en cliente, sin índice global. */
  import { api, mensajeError } from "../lib/api.js";
  import Escala from "../lib/Escala.svelte";
  import SliderDolor from "../lib/SliderDolor.svelte";
  import Chips from "../lib/Chips.svelte";
  import Icon from "../lib/Icon.svelte";

  const INDICADORES = [
    {
      clave: "calidad_sueno",
      nombre: "Calidad del sueño",
      pregunta: "¿Cómo has dormido?",
      etiquetas: { 1: "Muy mal", 2: "Mal", 3: "Regular", 4: "Bien", 5: "Muy bien" },
    },
    {
      clave: "recuperacion_fisica",
      nombre: "Recuperación física",
      pregunta: "¿Cómo notas tu recuperación?",
      etiquetas: {
        1: "Muy fatigado",
        2: "Fatigado",
        3: "Algo cansado",
        4: "Recuperado",
        5: "Totalmente recuperado",
      },
    },
    {
      clave: "energia_fisica",
      nombre: "Energía física",
      pregunta: "¿Cómo te encuentras físicamente?",
      etiquetas: { 1: "Agotado", 2: "Poca energía", 3: "Normal", 4: "Con energía", 5: "Excelente" },
    },
    {
      clave: "claridad_mental",
      nombre: "Claridad mental",
      pregunta: "¿Cómo te encuentras mentalmente?",
      etiquetas: {
        1: "Muy espeso",
        2: "Poco despejado",
        3: "Normal",
        4: "Despejado",
        5: "Muy despejado",
      },
    },
    {
      clave: "estres_previsto",
      nombre: "Estrés previsto",
      pregunta: "¿Qué exigencia mental esperas hoy?",
      etiquetas: { 1: "Muy baja", 2: "Baja", 3: "Normal", 4: "Alta", 5: "Muy alta" },
    },
  ];

  const ZONAS = [
    "lumbar",
    "cervical",
    "hombros",
    "brazos_manos",
    "cadera",
    "rodillas",
    "piernas_pies",
    "otras",
  ];
  const ETIQUETAS_ZONA = {
    lumbar: "Lumbar",
    cervical: "Cervical",
    hombros: "Hombros",
    brazos_manos: "Brazos/manos",
    cadera: "Cadera",
    rodillas: "Rodillas",
    piernas_pies: "Piernas/pies",
    otras: "Otras",
  };

  const NOMBRES = Object.fromEntries(INDICADORES.map((i) => [i.clave, i.nombre]));
  NOMBRES.molestias_fisicas = "Molestias físicas";

  const aISO = (d) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const HOY = aISO(new Date());
  const fmtFecha = new Intl.DateTimeFormat("es", { weekday: "short", day: "numeric", month: "short" });
  const legible = (fecha) => fmtFecha.format(new Date(fecha + "T00:00:00"));

  const nivelMolestias = (v) =>
    v === 0 ? "Sin molestias" : v <= 3 ? "Molestias leves" : v <= 6 ? "Molestias moderadas" : "Molestias intensas";

  // --- Formulario del día seleccionado -------------------------------------------------
  let fecha = $state(HOY);
  let valores = $state(Object.fromEntries(INDICADORES.map((i) => [i.clave, null])));
  // El deslizador no distingue «0» de «sin valorar»: se marca al tocarlo o al
  // cargar un registro que ya tenía dato.
  let molestias = $state(0);
  let molestiasValoradas = $state(false);
  let zonasMarcadas = $state({});
  let observaciones = $state("");
  let mostrarObservaciones = $state(false);

  let error = $state("");
  let aviso = $state("");
  let cargando = $state(false);

  function pintarRegistro(registro) {
    valores = Object.fromEntries(INDICADORES.map((i) => [i.clave, registro?.[i.clave] ?? null]));
    molestias = registro?.molestias_fisicas ?? 0;
    molestiasValoradas = registro?.molestias_fisicas != null;
    zonasMarcadas = Object.fromEntries(ZONAS.map((z) => [z, (registro?.zonas_molestias || []).includes(z)]));
    observaciones = registro?.observaciones || "";
    mostrarObservaciones = Boolean(registro?.observaciones);
  }

  async function cargarDia(f) {
    error = "";
    aviso = "";
    try {
      const datos = await api.get(`/api/bienestar/${f}`);
      pintarRegistro(datos.registro);
    } catch (e) {
      error = mensajeError(e);
    }
  }

  function moverFecha(delta) {
    const d = new Date(fecha + "T00:00:00");
    d.setDate(d.getDate() + delta);
    const nueva = aISO(d);
    if (nueva > HOY) return; // el registro es matutino: no hay futuro que valorar
    fecha = nueva;
  }

  $effect(() => {
    cargarDia(fecha);
  });

  async function guardar() {
    error = "";
    aviso = "";
    const cuerpo = {
      ...valores,
      molestias_fisicas: molestiasValoradas ? molestias : null,
      zonas_molestias:
        molestiasValoradas && molestias > 0 ? ZONAS.filter((z) => zonasMarcadas[z]) : [],
      observaciones: observaciones.trim() || null,
    };
    cargando = true;
    try {
      await api.put(`/api/bienestar/${fecha}`, cuerpo);
      aviso = "Guardado";
      cargarHistorial();
    } catch (e) {
      error = mensajeError(e);
    } finally {
      cargando = false;
    }
  }

  // --- Histórico y tendencias -----------------------------------------------------------
  let dias = $state([]);
  let periodo = $state(7);

  async function cargarHistorial() {
    try {
      const datos = await api.get("/api/bienestar?dias=30");
      dias = datos.dias;
    } catch {
      // Sin histórico visible: el formulario sigue funcionando.
    }
  }

  $effect(() => {
    cargarHistorial();
  });

  let tendencia = $derived.by(() => {
    const ventana = dias.slice(0, periodo);
    const conRegistro = ventana.filter((d) => d.registro);
    const medias = [...Object.keys(NOMBRES)].map((clave) => {
      const datos = conRegistro.map((d) => d.registro[clave]).filter((v) => v != null);
      return {
        clave,
        media: datos.length ? datos.reduce((a, b) => a + b, 0) / datos.length : null,
        n: datos.length,
      };
    });
    return { medias, registrados: conRegistro.length, total: ventana.length };
  });

  function resumenDia(registro) {
    if (!registro) return null;
    const partes = INDICADORES.filter((i) => registro[i.clave] != null).map(
      (i) => `${i.nombre} ${registro[i.clave]}`
    );
    if (registro.molestias_fisicas != null) partes.push(`Molestias ${registro.molestias_fisicas}`);
    return partes.length ? partes.join(" · ") : "Sin indicadores valorados";
  }
</script>

<h2 class="mb-1 font-display text-2xl font-bold tracking-wide">ESTADO DIARIO</h2>
<p class="mb-4 text-sm text-apagado">
  Registro matutino de bienestar. Es informativo: no cambia tu sesión de hoy.
</p>

<!-- Navegación por fecha: se puede consultar y corregir cualquier día pasado. -->
<div class="mb-5 flex items-center justify-between rounded-xl border border-borde bg-superficie px-3 py-2">
  <button type="button" onclick={() => moverFecha(-1)} aria-label="Día anterior" class="p-2 text-apagado">
    <Icon nombre="atras" tam={18} />
  </button>
  <p class="font-semibold capitalize">
    {legible(fecha)}{#if fecha === HOY} <span class="text-acento">· hoy</span>{/if}
  </p>
  <button
    type="button"
    onclick={() => moverFecha(1)}
    disabled={fecha === HOY}
    aria-label="Día siguiente"
    class="p-2 text-apagado disabled:opacity-30"
  >
    <span class="inline-block rotate-180"><Icon nombre="atras" tam={18} /></span>
  </button>
</div>

<form onsubmit={(e) => { e.preventDefault(); guardar(); }} class="space-y-6">
  {#each INDICADORES.slice(0, 2) as ind}
    <section>
      <p class="mb-1 text-xs font-semibold uppercase tracking-wider text-tenue">{ind.nombre}</p>
      <p class="mb-2 text-sm text-apagado">{ind.pregunta}</p>
      <Escala bind:valor={valores[ind.clave]} etiquetas={ind.etiquetas} />
    </section>
  {/each}

  <section>
    <p class="mb-1 text-xs font-semibold uppercase tracking-wider text-tenue">
      Molestias físicas{#if molestiasValoradas}
        · <span class="text-base font-bold normal-case text-texto">{molestias}</span>
      {/if}
    </p>
    <p class="mb-2 text-sm text-apagado">¿Tienes dolor o molestias?</p>
    <div oninput={() => (molestiasValoradas = true)}>
      <SliderDolor bind:valor={molestias} />
    </div>
    <p class="mt-1 text-xs {molestiasValoradas ? 'text-texto' : 'text-tenue'}">
      {molestiasValoradas ? nivelMolestias(molestias) : "Sin valorar (desliza para valorar)"}
    </p>
    {#if molestiasValoradas && molestias > 0}
      <p class="mb-2 mt-3 text-xs font-semibold uppercase tracking-wider text-tenue">
        ¿Dónde tienes molestias? (opcional)
      </p>
      <Chips tokens={ZONAS} bind:marcados={zonasMarcadas} etiquetas={ETIQUETAS_ZONA} />
    {/if}
  </section>

  {#each INDICADORES.slice(2) as ind}
    <section>
      <p class="mb-1 text-xs font-semibold uppercase tracking-wider text-tenue">{ind.nombre}</p>
      <p class="mb-2 text-sm text-apagado">{ind.pregunta}</p>
      <Escala bind:valor={valores[ind.clave]} etiquetas={ind.etiquetas} />
    </section>
  {/each}

  <section>
    <button
      type="button"
      onclick={() => (mostrarObservaciones = !mostrarObservaciones)}
      class="flex items-center gap-1.5 text-sm font-medium text-acento"
    >
      <Icon nombre={mostrarObservaciones ? "cerrar" : "plus"} tam={14} />
      Observaciones (opcional)
    </button>
    {#if mostrarObservaciones}
      <textarea
        bind:value={observaciones}
        rows="2"
        placeholder="Solo circunstancias excepcionales"
        class="mt-3 w-full rounded-xl border border-borde bg-superficie px-4 py-3 text-texto placeholder:text-tenue focus:border-acento focus:outline-none"
      ></textarea>
    {/if}
  </section>

  {#if error}
    <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
      <Icon nombre="aviso" tam={16} /> {error}
    </p>
  {/if}
  {#if aviso}
    <p class="flex items-center gap-2 rounded-lg bg-verde/10 p-3 text-sm text-verde">
      <Icon nombre="check" tam={16} /> {aviso}
    </p>
  {/if}

  <button
    type="submit"
    disabled={cargando}
    class="w-full rounded-xl bg-acento py-4 font-display text-xl font-bold tracking-wider text-fondo disabled:opacity-50"
  >
    {cargando ? "GUARDANDO…" : "GUARDAR ESTADO"}
  </button>
</form>

<!-- Tendencias por indicador (sin índice global, docs/morning_state §4). -->
<section class="mt-10">
  <div class="mb-3 flex items-center justify-between">
    <h3 class="font-display text-lg font-bold tracking-wide">TENDENCIAS</h3>
    <div class="flex gap-1">
      {#each [7, 14, 30] as p}
        <button
          type="button"
          onclick={() => (periodo = p)}
          class="rounded-lg px-3 py-1.5 text-xs font-semibold {periodo === p
            ? 'bg-acento text-fondo'
            : 'bg-superficie text-apagado border border-borde'}"
        >
          {p} días
        </button>
      {/each}
    </div>
  </div>
  <p class="mb-3 text-xs text-tenue">
    {tendencia.registrados} de {tendencia.total} días con registro; los días sin registro no cuentan como 0.
  </p>
  <div class="space-y-2">
    {#each tendencia.medias as m}
      <div class="flex items-center justify-between rounded-xl border border-borde bg-superficie px-4 py-2.5">
        <span class="text-sm">{NOMBRES[m.clave]}</span>
        <span class="text-sm font-semibold {m.media == null ? 'text-tenue' : 'text-texto'}">
          {m.media == null ? "sin datos" : `${m.media.toFixed(1)} · ${m.n} días`}
        </span>
      </div>
    {/each}
  </div>
</section>

<!-- Últimos 7 días: tocar uno lo carga en el formulario para consultarlo o corregirlo. -->
<section class="mt-8">
  <h3 class="mb-3 font-display text-lg font-bold tracking-wide">ÚLTIMOS 7 DÍAS</h3>
  <div class="space-y-2">
    {#each dias.slice(0, 7) as d}
      <button
        type="button"
        onclick={() => (fecha = d.fecha)}
        class="w-full rounded-xl border px-4 py-3 text-left transition-colors {fecha === d.fecha
          ? 'border-acento bg-acento/10'
          : 'border-borde bg-superficie'}"
      >
        <p class="text-sm font-semibold capitalize">{legible(d.fecha)}</p>
        <p class="mt-0.5 text-xs {d.registro ? 'text-apagado' : 'text-tenue italic'}">
          {d.registro ? resumenDia(d.registro) : "Sin registro"}
        </p>
      </button>
    {/each}
  </div>
</section>
