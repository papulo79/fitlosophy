<script>
  import { api, mensajeError } from "../lib/api.js";
  import { flujo, reiniciarFlujo } from "../lib/stores.svelte.js";
  import Opciones from "../lib/Opciones.svelte";

  let sesion = $derived(flujo.sesion);

  let sensacion = $state(null);
  let molestias = $state([]); // [{zona, intensidad}]
  let resultado = $state(null);
  let error = $state("");
  let cargando = $state(false);

  function anadirMolestia() {
    molestias = [...molestias, { zona: "", intensidad: 3 }];
  }

  function quitarMolestia(i) {
    molestias = molestias.filter((_, j) => j !== i);
  }

  async function enviar() {
    error = "";
    if (!sensacion) {
      error = "Indica la sensación respecto a lo previsto.";
      return;
    }
    for (const m of molestias) {
      if (!m.zona.trim()) {
        error = "Toda molestia necesita una zona.";
        return;
      }
    }
    cargando = true;
    try {
      resultado = await api.post(`/api/sesiones/${sesion.id}/cierre`, {
        sensacion,
        molestias: molestias.map((m) => ({ zona: m.zona.trim(), intensidad: m.intensidad })),
      });
      flujo.sesion = { ...flujo.sesion, estado: "cerrada" };
    } catch (e) {
      error = mensajeError(e);
    } finally {
      cargando = false;
    }
  }

  function nuevoDia() {
    reiniciarFlujo();
    location.hash = "#/estado";
  }
</script>

{#if sesion}
  {#if resultado}
    <div class="space-y-5">
      <h2 class="text-xl font-bold">Sesión cerrada</h2>
      {#if resultado.dimensiones_congeladas?.length}
        <div class="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-800">
          <p class="font-semibold">Ventanas congeladas por molestias (la dimensión no estará disponible unos días):</p>
          <p class="mt-1">{resultado.dimensiones_congeladas.join(", ")}</p>
        </div>
      {:else}
        <p class="rounded-xl border border-gray-200 bg-white p-4 text-sm text-gray-600">Sin dimensiones congeladas.</p>
      {/if}
      {#if resultado.zonas_sin_mapear?.length}
        <p class="rounded-xl border border-gray-200 bg-white p-4 text-sm text-gray-600">
          {resultado.nota} Zonas: {resultado.zonas_sin_mapear.join(", ")}.
        </p>
      {/if}
      <div class="flex gap-2">
        <a href="#/historial" class="flex-1 rounded-xl border border-gray-300 py-3 text-center font-medium">Ver historial</a>
        <button onclick={nuevoDia} class="flex-1 rounded-xl bg-blue-600 py-3 font-semibold text-white">Nuevo día</button>
      </div>
    </div>
  {:else}
    <div class="space-y-6">
      <h2 class="text-xl font-bold">Cierre de la sesión</h2>

      <section>
        <p class="mb-2 text-sm font-semibold text-gray-600">¿Cómo ha ido respecto a lo previsto?</p>
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
        <p class="mb-2 text-sm font-semibold text-gray-600">Molestias posteriores</p>
        {#each molestias as m, i}
          <div class="mb-2 flex items-center gap-2">
            <input bind:value={m.zona} type="text" placeholder="Zona (ej. lumbar)" class="min-w-0 flex-1 rounded-xl border border-gray-300 px-3 py-3" />
            <input bind:value={m.intensidad} type="number" min="0" max="10" class="w-20 rounded-xl border border-gray-300 px-3 py-3" />
            <button onclick={() => quitarMolestia(i)} aria-label="Quitar" class="rounded-lg border border-gray-300 px-3 py-3">✕</button>
          </div>
        {/each}
        <button onclick={anadirMolestia} class="text-sm font-medium text-blue-600">+ Añadir molestia</button>
      </section>

      {#if error}
        <p class="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>
      {/if}

      <button onclick={enviar} disabled={cargando} class="w-full rounded-xl bg-blue-600 py-4 text-lg font-bold text-white disabled:opacity-50">
        {cargando ? "Guardando…" : "Guardar cierre"}
      </button>
    </div>
  {/if}
{/if}
