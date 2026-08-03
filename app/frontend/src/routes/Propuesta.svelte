<script>
  import { api, mensajeError } from "../lib/api.js";
  import { flujo } from "../lib/stores.svelte.js";
  import { BLOQUES, FAMILIAS, agruparPorBloque } from "../lib/etiquetas.js";
  import { urlBusqueda } from "../lib/busqueda.js";
  import Icon from "../lib/Icon.svelte";

  let propuesta = $derived(flujo.propuesta);
  let grupos = $derived(agruparPorBloque(propuesta?.items));

  // Modal de sustitución (criterio 8 de docs/14: motivo del rechazo visible).
  let modalIndice = $state(null);
  let catalogo = $state([]);
  let candidato = $state("");
  let motivos = $state([]);
  let errorModal = $state("");
  let error = $state("");
  let cargando = $state(false);

  async function abrirSustitucion(indice) {
    modalIndice = indice;
    candidato = "";
    motivos = [];
    errorModal = "";
    if (catalogo.length === 0) {
      try {
        const resp = await api.get("/api/ejercicios");
        catalogo = resp.ejercicios;
      } catch (e) {
        errorModal = mensajeError(e);
      }
    }
  }

  async function sustituir() {
    if (!candidato) return;
    errorModal = "";
    motivos = [];
    try {
      const resp = await api.post(`/api/propuestas/${propuesta.id}/sustituir`, {
        item_indice: modalIndice,
        exercise_id: candidato,
      });
      flujo.propuesta = resp.propuesta;
      modalIndice = null;
    } catch (e) {
      if (e.status === 409 && e.detail && typeof e.detail === "object") {
        motivos = e.detail.motivos || [];
      } else {
        errorModal = mensajeError(e);
      }
    }
  }

  async function empezar() {
    error = "";
    cargando = true;
    try {
      const resp = await api.post("/api/sesiones", { proposal_id: propuesta.id });
      flujo.sesion = resp.sesion;
      location.hash = "#/ejecucion";
    } catch (e) {
      error = mensajeError(e);
    } finally {
      cargando = false;
    }
  }

</script>

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
                <a href={urlBusqueda(item.nombre)} target="_blank" rel="noopener" title="Buscar vídeo del ejercicio" class="group flex items-center gap-1.5 font-semibold text-texto">
                  {item.nombre}
                  <span class="text-tenue group-hover:text-acento"><Icon nombre="buscar" tam={13} /></span>
                </a>
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
