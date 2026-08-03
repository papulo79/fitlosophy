<script>
  import { api, mensajeError } from "../lib/api.js";
  import { flujo } from "../lib/stores.svelte.js";
  import Opciones from "../lib/Opciones.svelte";
  import SliderDolor from "../lib/SliderDolor.svelte";
  import Chips from "../lib/Chips.svelte";
  import Icon from "../lib/Icon.svelte";
  import { RECUPERACION } from "../lib/etiquetas.js";

  const ETIQUETAS_MATERIAL = {
    trx: "TRX",
    tatami: "Tatami",
    barra_dominadas: "Barra de dominadas",
    kettlebell: "Kettlebells",
    comba: "Comba",
    caja: "Caja",
    goma: "Gomas",
    conos: "Conos",
    escalera_agilidad: "Escalera de agilidad",
    cinta: "Cinta",
  };

  let recuperacion = $state(null);
  let dolor = $state(0);
  let zonaDolor = $state("");
  let bjj = $state(null);
  let tipoBjj = $state("normal");
  let limitacion = $state("");
  let sueno = $state("");
  let tiempo = $state("");
  let preferencia = $state("");
  let circunstancias = $state("");
  let mostrarOpcionales = $state(false);

  let material = $state([]); // tokens del inventario del perfil
  let marcados = $state({}); // token -> true/false
  let error = $state("");
  let cargando = $state(false);

  $effect(() => {
    api
      .get("/api/perfil")
      .then((p) => {
        material = p.material || [];
        marcados = Object.fromEntries(material.map((t) => [t, true]));
      })
      .catch(() => {});
  });

  let materialVariable = $derived(material.filter((t) => t !== "tatami"));
  let todoMarcado = $derived(materialVariable.every((t) => marcados[t]));

  async function enviar(e) {
    e.preventDefault();
    error = "";
    if (!recuperacion) {
      error = "Indica cómo has dormido / cómo estás recuperado.";
      return;
    }
    if (!bjj) {
      error = "Indica si hay BJJ hoy.";
      return;
    }
    if (dolor > 0 && !zonaDolor.trim()) {
      error = "Si el dolor es mayor que 0 hay que indicar la zona.";
      return;
    }
    const cuerpo = {
      recuperacion,
      dolor,
      bjj_disponible: bjj,
      zona_dolor: dolor > 0 ? zonaDolor.trim() : null,
      tipo_bjj: bjj === "si" ? tipoBjj : null,
      limitacion: limitacion.trim() || null,
      sueno: sueno.trim() || null,
      tiempo_disponible: tiempo ? Number(tiempo) : null,
      preferencia: preferencia.trim() || null,
      circunstancias: circunstancias.trim() || null,
    };
    // Todo marcado = no se envía (todo el garaje); nada marcado = sin material.
    if (!todoMarcado) {
      cuerpo.material_disponible = materialVariable.filter((t) => marcados[t]);
    }
    cargando = true;
    try {
      const resp = await api.post("/api/estado-diario", cuerpo);
      flujo.estadoDiarioId = resp.estado_diario_id;
      flujo.propuesta = resp.propuesta;
      flujo.sesion = null;
      location.hash = "#/propuesta";
    } catch (e2) {
      error = mensajeError(e2);
    } finally {
      cargando = false;
    }
  }
</script>

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
