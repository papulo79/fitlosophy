<script>
  import { api, mensajeError } from "../lib/api.js";
  import Icon from "../lib/Icon.svelte";
  import {
    EQUIPMENT_CANDIDATOS,
    GRUPOS_MUSCULARES,
    PATRONES,
    IMPACTO_LUMBAR,
    COMPATIBILIDAD_BJJ,
    NIVELES,
    LATERALIDAD,
  } from "../lib/etiquetas.js";

  // Revisión de candidatos importados (docs/15): la aceptación aquí es la
  // revisión humana que escribe en data/ejercicios.yaml.

  let lista = $state([]);
  let contadores = $state({ equipment: {}, muscle_group: {} });
  let error = $state("");
  let estado = $state("pendiente_revision");
  let material = $state(null); // equipment seleccionado
  let grupo = $state(null); // muscle_group seleccionado
  let patronFiltro = $state("");
  let detalle = $state(null);
  let valores = $state(null);

  // Formulario de revisión (etiquetas editables).
  let forma = $state(null);
  let erroresRevision = $state([]);
  let mensaje = $state("");
  let ocupado = $state(false);

  const EQUIPAMIENTO_ORDEN = ["body weight", "weighted", "kettlebell", "band", "resistance band", "rope"];

  function etiquetaEquipment(eq) {
    return EQUIPMENT_CANDIDATOS[eq] || eq;
  }
  function etiquetaGrupo(g) {
    return GRUPOS_MUSCULARES[g] || g || "Sin grupo";
  }

  async function cargar() {
    error = "";
    try {
      const params = new URLSearchParams();
      if (estado) params.set("estado", estado);
      if (material) params.set("equipment", material);
      if (grupo) params.set("grupo", grupo);
      const r = await api.get(`/api/candidatos?${params}`);
      lista = r.candidatos;
      contadores = r.contadores;
    } catch (e) {
      error = mensajeError(e);
    }
  }

  $effect(() => {
    estado;
    material;
    grupo;
    if (!detalle) cargar();
  });

  let filtrados = $derived(
    patronFiltro ? lista.filter((c) => c.patron_inferido === patronFiltro) : lista
  );

  let gruposDisponibles = $derived(
    Object.keys(contadores.muscle_group || {}).sort(
      (a, b) => (contadores.muscle_group[b] || 0) - (contadores.muscle_group[a] || 0)
    )
  );

  let materialesDisponibles = $derived(
    Object.keys(contadores.equipment || {}).sort(
      (a, b) => EQUIPAMIENTO_ORDEN.indexOf(a) - EQUIPAMIENTO_ORDEN.indexOf(b)
    )
  );

  async function abrir(c) {
    erroresRevision = [];
    mensaje = "";
    try {
      detalle = await api.get(`/api/candidatos/${c.id}`);
      valores = detalle.valores;
      const base = detalle.etiquetas_finales || detalle.etiquetas_inferidas || {};
      forma = {
        nombre: detalle.nombre_es,
        descripcion: base.descripcion || "",
        patron: base.patron || "",
        nivel: base.nivel || "base",
        lateralidad: base.lateralidad || "bilateral",
        impacto_lumbar: base.impacto_lumbar || "amarillo",
        compatibilidad_bjj: base.compatibilidad_bjj || "si",
      };
    } catch (e) {
      error = mensajeError(e);
    }
  }

  function volver() {
    detalle = null;
    forma = null;
    cargar();
  }

  async function guardarEtiquetas() {
    await api.put(`/api/candidatos/${detalle.id}`, { etiquetas_finales: { ...forma } });
  }

  async function aceptar() {
    ocupado = true;
    erroresRevision = [];
    mensaje = "";
    try {
      await guardarEtiquetas();
      const r = await api.post(`/api/candidatos/${detalle.id}/aceptar`);
      mensaje = `Aceptado como «${r.exercise_id}».`;
      volver();
    } catch (e) {
      const d = e?.detail;
      if (d && Array.isArray(d.errores)) erroresRevision = d.errores;
      else error = mensajeError(e);
    } finally {
      ocupado = false;
    }
  }

  async function descartar() {
    ocupado = true;
    erroresRevision = [];
    mensaje = "";
    try {
      await api.post(`/api/candidatos/${detalle.id}/descartar`, { motivo: motivoDescarte || null });
      mensaje = "Candidato descartado.";
      volver();
    } catch (e) {
      error = mensajeError(e);
    } finally {
      ocupado = false;
    }
  }

  let motivoDescarte = $state("");
</script>

<div class="space-y-4">
  <div class="flex items-baseline justify-between gap-2">
    <h2 class="font-display text-2xl font-bold tracking-wide">CANDIDATOS</h2>
    <a href="#/perfil" class="text-sm text-apagado">← Perfil</a>
  </div>

  {#if mensaje}
    <p class="flex items-center gap-2 rounded-lg bg-verde/10 p-3 text-sm text-verde">
      <Icon nombre="check" tam={16} /> {mensaje}
    </p>
  {/if}
  {#if error}
    <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
      <Icon nombre="aviso" tam={16} /> {error}
    </p>
  {/if}

  {#if !detalle}
    <p class="text-sm text-apagado">
      Ejercicios importados del dataset, pendientes de tu revisión. Aceptar escribe en el catálogo;
      descartar lo archiva. GIFs © Gym visual — gymvisual.com.
    </p>

    <div class="flex gap-2 text-sm">
      {#each [["pendiente_revision", "Pendientes"], ["aceptado", "Aceptados"], ["descartado", "Descartados"]] as [v, txt]}
        <button
          onclick={() => { estado = v; material = null; grupo = null; }}
          class="rounded-full border px-3 py-1 {estado === v ? 'border-acento bg-acento/10 text-acento' : 'border-borde text-apagado'}"
        >{txt}</button>
      {/each}
    </div>

    <!-- Nivel 1: material -->
    <div class="flex flex-wrap gap-2 text-sm">
      {#each materialesDisponibles as m}
        <button
          onclick={() => { material = material === m ? null : m; grupo = null; }}
          class="rounded-full border px-3 py-1 {material === m ? 'border-acento bg-acento/10 text-acento' : 'border-borde text-apagado'}"
        >{etiquetaEquipment(m)} ({contadores.equipment[m]})</button>
      {/each}
    </div>

    <!-- Nivel 2: grupo muscular dentro del material -->
    {#if grupo !== null || material}
      <div class="flex flex-wrap gap-2 text-xs">
        {#each gruposDisponibles as g}
          <button
            onclick={() => (grupo = grupo === g ? null : g)}
            class="rounded-full border px-2.5 py-1 {grupo === g ? 'border-acento bg-acento/10 text-acento' : 'border-borde text-tenue'}"
          >{etiquetaGrupo(g)} ({contadores.muscle_group[g]})</button>
        {/each}
      </div>
    {/if}

    <select bind:value={patronFiltro} class="w-full rounded-xl border border-borde bg-superficie p-2 text-sm text-texto">
      <option value="">Todos los patrones</option>
      {#each Object.entries(PATRONES) as [v, txt]}
        <option value={v}>{txt}</option>
      {/each}
    </select>

    <ul class="space-y-2">
      {#each filtrados as c (c.id)}
        <li>
          <button onclick={() => abrir(c)} class="flex w-full items-center gap-3 rounded-xl border border-borde bg-superficie p-2 text-left">
            {#if c.gif}
              <img src={`/api/candidatos/${c.id}/gif`} alt="" class="h-14 w-14 rounded-lg bg-fondo object-cover" loading="lazy" />
            {/if}
            <span class="min-w-0 flex-1">
              <span class="block truncate font-medium">{c.nombre_es}</span>
              <span class="block text-xs text-tenue">
                {etiquetaGrupo(c.muscle_group)} · {PATRONES[c.patron_inferido] || "—"}
              </span>
            </span>
            {#if c.posible_equivalente}
              <span class="rounded-full border border-ambar/40 bg-ambar/10 px-2 py-0.5 text-[10px] text-ambar" title={`Posible equivalente: ${c.posible_equivalente}`}>
                duplicado?
              </span>
            {/if}
          </button>
        </li>
      {:else}
        <li class="text-sm text-tenue">No hay candidatos con este filtro.</li>
      {/each}
    </ul>
  {:else}
    <!-- Detalle y revisión -->
    <div class="space-y-3 rounded-xl border border-borde bg-superficie p-3">
      <div class="flex items-start gap-3">
        {#if detalle.gif}
          <img src={`/api/candidatos/${detalle.id}/gif`} alt={detalle.nombre_es} class="h-32 w-32 rounded-lg bg-fondo object-cover" />
        {/if}
        <div class="min-w-0 flex-1 text-sm">
          <p class="font-medium">{detalle.nombre_en}</p>
          <p class="text-xs text-tenue">
            {etiquetaEquipment(detalle.equipment)} · {etiquetaGrupo(detalle.muscle_group)}
            · material: {detalle.material_fitlosophy.length ? detalle.material_fitlosophy.join(", ") : "sin material"}
          </p>
          {#if detalle.posible_equivalente}
            <p class="mt-1 rounded-lg border border-ambar/40 bg-ambar/10 p-1.5 text-xs text-ambar">
              Posible equivalente en el catálogo: <code>{detalle.posible_equivalente}</code>
            </p>
          {/if}
          <p class="mt-1 text-[10px] text-tenue">© Gym visual — gymvisual.com</p>
        </div>
      </div>
      {#if detalle.instrucciones_es}
        <p class="whitespace-pre-line text-xs text-apagado">{detalle.instrucciones_es}</p>
      {/if}
    </div>

    {#if detalle.estado === "pendiente_revision" && forma}
      <div class="space-y-3 rounded-xl border border-borde bg-superficie p-3 text-sm">
        <label class="block">
          <span class="text-xs text-tenue">Nombre en español</span>
          <input bind:value={forma.nombre} class="mt-1 w-full rounded-lg border border-borde bg-fondo p-2 text-texto" />
        </label>
        <label class="block">
          <span class="text-xs text-tenue">Descripción (ejecución, con el límite en palabras si es rojo)</span>
          <textarea bind:value={forma.descripcion} rows="3" class="mt-1 w-full rounded-lg border border-borde bg-fondo p-2 text-texto"></textarea>
        </label>
        <div class="grid grid-cols-2 gap-2">
          <label class="block">
            <span class="text-xs text-tenue">Patrón</span>
            <select bind:value={forma.patron} class="mt-1 w-full rounded-lg border border-borde bg-fondo p-2">
              {#each valores?.patron || [] as v}<option value={v}>{PATRONES[v] || v}</option>{/each}
            </select>
          </label>
          <label class="block">
            <span class="text-xs text-tenue">Nivel</span>
            <select bind:value={forma.nivel} class="mt-1 w-full rounded-lg border border-borde bg-fondo p-2">
              {#each valores?.nivel || [] as v}<option value={v}>{NIVELES[v] || v}</option>{/each}
            </select>
          </label>
          <label class="block">
            <span class="text-xs text-tenue">Lateralidad</span>
            <select bind:value={forma.lateralidad} class="mt-1 w-full rounded-lg border border-borde bg-fondo p-2">
              {#each valores?.lateralidad || [] as v}<option value={v}>{LATERALIDAD[v] || v}</option>{/each}
            </select>
          </label>
          <label class="block">
            <span class="text-xs text-tenue">Impacto lumbar</span>
            <select bind:value={forma.impacto_lumbar} class="mt-1 w-full rounded-lg border border-borde bg-fondo p-2">
              {#each valores?.impacto_lumbar || [] as v}<option value={v}>{IMPACTO_LUMBAR[v] || v}</option>{/each}
            </select>
          </label>
          <label class="block">
            <span class="text-xs text-tenue">Compatibilidad BJJ</span>
            <select bind:value={forma.compatibilidad_bjj} class="mt-1 w-full rounded-lg border border-borde bg-fondo p-2">
              {#each valores?.compatibilidad_bjj || [] as v}<option value={v}>{COMPATIBILIDAD_BJJ[v] || v}</option>{/each}
            </select>
          </label>
        </div>

        {#if erroresRevision.length}
          <div class="rounded-lg bg-rojo/10 p-2 text-xs text-rojo">
            <p class="font-semibold">La validación del catálogo lo rechaza:</p>
            <ul class="list-disc pl-4">
              {#each erroresRevision as err}<li>{err}</li>{/each}
            </ul>
          </div>
        {/if}

        <div class="flex gap-2">
          <button onclick={aceptar} disabled={ocupado} class="flex-1 rounded-xl bg-acento py-2.5 font-semibold text-fondo disabled:opacity-50">
            Aceptar y añadir al catálogo
          </button>
          <button onclick={descartar} disabled={ocupado} class="rounded-xl border border-rojo/40 px-4 py-2.5 font-medium text-rojo disabled:opacity-50">
            Descartar
          </button>
        </div>
        <input bind:value={motivoDescarte} placeholder="Motivo del descarte (opcional)" class="w-full rounded-lg border border-borde bg-fondo p-2 text-xs text-texto" />
      </div>
    {:else}
      <p class="text-sm text-apagado">
        Estado: {detalle.estado}
        {#if detalle.motivo_descarte}· motivo: {detalle.motivo_descarte}{/if}
      </p>
    {/if}

    <button onclick={volver} class="w-full rounded-xl border border-borde bg-superficie py-2.5 text-sm font-medium text-apagado">
      Volver a la lista
    </button>
  {/if}
</div>
