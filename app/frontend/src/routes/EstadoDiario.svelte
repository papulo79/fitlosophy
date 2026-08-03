<script>
  import { api, mensajeError } from "../lib/api.js";
  import { flujo } from "../lib/stores.svelte.js";
  import Opciones from "../lib/Opciones.svelte";

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

<h2 class="mb-4 text-xl font-bold">¿Cómo estás hoy?</h2>

<form onsubmit={enviar} class="space-y-6">
  <section>
    <p class="mb-2 text-sm font-semibold text-gray-600">Recuperación</p>
    <Opciones
      bind:valor={recuperacion}
      opciones={[
        { valor: "verde", etiqueta: "Verde" },
        { valor: "amarillo", etiqueta: "Amarillo" },
        { valor: "rojo", etiqueta: "Rojo" },
      ]}
      colores={{
        verde: "border-green-600 bg-green-600 text-white",
        amarillo: "border-amber-500 bg-amber-500 text-white",
        rojo: "border-red-600 bg-red-600 text-white",
      }}
    />
  </section>

  <section>
    <p class="mb-2 text-sm font-semibold text-gray-600">Dolor (0 = nada, 10 = mucho): <span class="text-base font-bold">{dolor}</span></p>
    <input bind:value={dolor} type="range" min="0" max="10" step="1" class="w-full" />
    {#if dolor > 0}
      <input
        bind:value={zonaDolor}
        type="text"
        placeholder="Zona del dolor (obligatorio)"
        class="mt-2 w-full rounded-xl border border-gray-300 px-4 py-3"
      />
    {/if}
  </section>

  <section>
    <p class="mb-2 text-sm font-semibold text-gray-600">¿Hay BJJ hoy?</p>
    <Opciones
      bind:valor={bjj}
      opciones={[
        { valor: "si", etiqueta: "Sí" },
        { valor: "no", etiqueta: "No" },
        { valor: "incierto", etiqueta: "Incierto" },
      ]}
    />
    {#if bjj === "si"}
      <p class="mt-3 mb-2 text-sm font-semibold text-gray-600">Tipo de sesión de BJJ</p>
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
      <p class="mb-2 text-sm font-semibold text-gray-600">Material disponible hoy</p>
      <div class="grid grid-cols-2 gap-2">
        {#each materialVariable as token}
          <label class="flex items-center gap-2 rounded-xl border border-gray-300 bg-white px-3 py-3 text-sm">
            <input type="checkbox" bind:checked={marcados[token]} class="h-5 w-5" />
            {ETIQUETAS_MATERIAL[token] || token}
          </label>
        {/each}
        <label class="flex items-center gap-2 rounded-xl border border-gray-200 bg-gray-100 px-3 py-3 text-sm text-gray-500">
          <input type="checkbox" checked disabled class="h-5 w-5" />
          Tatami (siempre)
        </label>
      </div>
    </section>
  {/if}

  <section>
    <button type="button" onclick={() => (mostrarOpcionales = !mostrarOpcionales)} class="text-sm font-medium text-blue-600">
      {mostrarOpcionales ? "− Ocultar opcionales" : "+ Limitación, sueño, tiempo, preferencias…"}
    </button>
    {#if mostrarOpcionales}
      <div class="mt-3 space-y-3">
        <input bind:value={limitacion} type="text" placeholder="Limitación puntual (ej. hombro cargado)" class="w-full rounded-xl border border-gray-300 px-4 py-3" />
        <input bind:value={sueno} type="text" placeholder="Sueño (ej. 6 h, mal)" class="w-full rounded-xl border border-gray-300 px-4 py-3" />
        <input bind:value={tiempo} type="number" min="1" placeholder="Tiempo disponible (minutos)" class="w-full rounded-xl border border-gray-300 px-4 py-3" />
        <input bind:value={preferencia} type="text" placeholder="Preferencia (ej. sin impacto)" class="w-full rounded-xl border border-gray-300 px-4 py-3" />
        <input bind:value={circunstancias} type="text" placeholder="Circunstancias (ej. viaje, calor)" class="w-full rounded-xl border border-gray-300 px-4 py-3" />
      </div>
    {/if}
  </section>

  {#if error}
    <p class="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>
  {/if}

  <button type="submit" disabled={cargando} class="w-full rounded-xl bg-blue-600 py-4 text-lg font-bold text-white disabled:opacity-50">
    {cargando ? "Decidiendo…" : "Proponer sesión"}
  </button>
</form>
