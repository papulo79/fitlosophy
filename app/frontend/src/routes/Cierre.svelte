<script>
  import { api, mensajeError } from "../lib/api.js";
  import { flujo, reiniciarFlujo } from "../lib/stores.svelte.js";
  import Opciones from "../lib/Opciones.svelte";
  import Icon from "../lib/Icon.svelte";

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
