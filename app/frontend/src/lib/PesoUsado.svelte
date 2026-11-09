<script>
  /**
   * Peso usado en el ejercicio, apuntado en línea.
   *
   * El catálogo no prescribe kilos (docs/05): se apunta lo que se usó para
   * poder analizar la progresión. En ejercicios con kettlebell el número es
   * **kilos por kettlebell** y se acompaña de cuántas se usaron (1 o 2), de
   * modo que el total (12 × 2 = 24) no se pierde.
   *
   * Hoy no alimenta el modelo de carga (docs/12 es ciego a la intensidad).
   */
  import Icon from "./Icon.svelte";

  let { valor = null, unidades = 1, sugerencias = [], guardando = false, alGuardar } = $props();

  let editando = $state(false);
  let borrador = $state("");
  let nUnidades = $state(1);

  function abrir() {
    borrador = valor ?? "";
    nUnidades = unidades ?? 1;
    editando = true;
  }

  async function confirmar(kg) {
    const n = Number(kg);
    if (!Number.isFinite(n) || n < 0) return;
    await alGuardar(n, nUnidades);
    editando = false;
  }
</script>

{#if editando}
  <div class="mt-2 rounded-lg border border-borde bg-fondo p-2">
    <div class="flex items-center gap-2">
      <input
        bind:value={borrador}
        type="number"
        min="0"
        step="0.5"
        inputmode="decimal"
        placeholder="kg"
        class="min-h-11 w-24 rounded-lg border border-borde bg-superficie px-3 text-texto placeholder:text-tenue"
      />
      <button
        type="button"
        onclick={() => (nUnidades = nUnidades === 1 ? 2 : 1)}
        aria-label="Número de kettlebells"
        class="min-h-11 rounded-lg border px-3 text-sm font-semibold {nUnidades === 2
          ? 'border-acento bg-acento/15 text-acento'
          : 'border-borde text-apagado'}"
      >
        × {nUnidades} KB
      </button>
      <button
        onclick={() => confirmar(borrador)}
        disabled={guardando || borrador === ""}
        class="min-h-11 flex-1 rounded-lg bg-acento px-3 text-sm font-semibold text-fondo disabled:opacity-50"
      >
        {guardando ? "Guardando…" : "Guardar"}
      </button>
      <button onclick={() => (editando = false)} aria-label="Cancelar" class="flex min-h-11 items-center rounded-lg border border-borde px-3 text-apagado">
        <Icon nombre="cerrar" tam={16} />
      </button>
    </div>

    {#if nUnidades > 1 && borrador !== ""}
      <p class="mt-1.5 text-xs text-tenue">Total: {Number(borrador) * nUnidades} kg ({borrador} × {nUnidades})</p>
    {/if}

    {#if sugerencias.length}
      <!-- Inventario del perfil (8/12/16 kg): un toque en vez de teclear. -->
      <div class="mt-2 flex flex-wrap gap-1.5">
        {#each sugerencias as kg}
          <button
            onclick={() => confirmar(kg)}
            disabled={guardando}
            class="min-h-8 rounded-md border border-borde px-2.5 text-xs font-semibold text-apagado hover:border-acento hover:text-acento disabled:opacity-50"
          >
            {kg} kg
          </button>
        {/each}
      </div>
    {/if}
  </div>
{:else}
  <button onclick={abrir} class="mt-1.5 flex min-h-8 items-center gap-1.5 text-xs font-semibold {valor != null ? 'text-acento' : 'text-tenue hover:text-acento'}">
    <Icon nombre={valor != null ? "corregir" : "plus"} tam={12} />
    {valor != null ? `${valor} kg${unidades > 1 ? ` × ${unidades} (${valor * unidades} kg)` : ""}` : "Apuntar peso"}
  </button>
{/if}
