<script>
  import { api, mensajeError } from "../lib/api.js";
  import { flujo } from "../lib/stores.svelte.js";
  import { BLOQUES, FAMILIAS, ESTADOS_ITEM, agruparPorBloque } from "../lib/etiquetas.js";
  import Opciones from "../lib/Opciones.svelte";
  import Icon from "../lib/Icon.svelte";
  import BarraProgreso from "../lib/BarraProgreso.svelte";
  import AccionesEjercicio from "../lib/AccionesEjercicio.svelte";

  let sesion = $derived(flujo.sesion);
  let grupos = $derived(agruparPorBloque(sesion?.items));
  let hechos = $derived((sesion?.items || []).filter((i) => i.estado !== "pendiente").length);
  let total = $derived((sesion?.items || []).length);

  let error = $state("");
  let advertencias = $state([]);

  // Modal de desviación: el check es la acción por defecto; el modal es para desviarse.
  let itemModal = $state(null); // ítem abierto
  let modo = $state("modificado"); // modificado | sustituido | no_realizado
  let catalogo = $state([]);
  let formulario = $state({ series: "", repeticiones: "", segundos: "", minutos: "", carga_kg: "", exercise_id: "", motivo: "" });
  let errorModal = $state("");

  // Finalizar: RPE real obligatorio.
  let finalizando = $state(false);
  let rpe = $state(7);
  let cargando = $state(false);

  async function marcar(item) {
    if (item.estado !== "pendiente") return; // un check es definitivo; correcciones vía historial
    error = "";
    try {
      const resp = await api.patch(`/api/sesiones/${sesion.id}/items/${item.id}`, { estado: "completado" });
      flujo.sesion = resp.sesion;
      advertencias = resp.advertencias || [];
    } catch (e) {
      error = mensajeError(e);
    }
  }

  async function abrirModal(item) {
    if (sesion.estado !== "en_curso") return;
    itemModal = item;
    modo = "modificado";
    formulario = { series: "", repeticiones: "", segundos: "", minutos: "", carga_kg: "", exercise_id: "", motivo: "" };
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

  async function guardarDesviacion() {
    errorModal = "";
    const cuerpo = { estado: modo, motivo: formulario.motivo.trim() || null };
    if (modo === "sustituido") {
      if (!formulario.exercise_id) {
        errorModal = "Elige el ejercicio realizado.";
        return;
      }
      cuerpo.exercise_id_real = formulario.exercise_id;
    }
    if (modo === "modificado" || modo === "sustituido") {
      for (const [campo, clave] of [
        ["series", "series_real"],
        ["repeticiones", "repeticiones_real"],
        ["segundos", "segundos_real"],
        ["minutos", "minutos_real"],
        ["carga_kg", "carga_kg_real"],
      ]) {
        if (formulario[campo] !== "" && formulario[campo] !== null) cuerpo[clave] = Number(formulario[campo]);
      }
      if (modo === "modificado" && !Object.keys(cuerpo).some((k) => k.endsWith("_real"))) {
        errorModal = "Indica al menos un valor real.";
        return;
      }
    }
    try {
      const resp = await api.patch(`/api/sesiones/${sesion.id}/items/${itemModal.id}`, cuerpo);
      flujo.sesion = resp.sesion;
      advertencias = resp.advertencias || [];
      itemModal = null;
    } catch (e) {
      errorModal = mensajeError(e);
    }
  }

  async function finalizar() {
    error = "";
    cargando = true;
    try {
      const resp = await api.post(`/api/sesiones/${sesion.id}/finalizar`, { rpe_real: rpe });
      flujo.sesion = resp.sesion;
      location.hash = "#/cierre";
    } catch (e) {
      error = mensajeError(e);
    } finally {
      cargando = false;
    }
  }
</script>

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
            <div class="rounded-xl border border-borde bg-superficie p-3 {item.estado !== 'pendiente' ? 'opacity-60' : ''}">
              <div class="flex items-center gap-3">
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
              <AccionesEjercicio nombre={item.nombre} descripcion={item.descripcion} patrones={item.patrones} />
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
