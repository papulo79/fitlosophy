<script>
  /**
   * Peso usado en el ejercicio, apuntado en línea.
   *
   * Antes solo se llegaba a este dato abriendo el modal de desviación, que
   * obliga a declarar el ítem como «modificado»: semánticamente falso cuando lo
   * has hecho tal cual y solo quieres dejar constancia de los kilos. El backend
   * ya aceptaba `estado: completado` con `carga_kg_real`, faltaba la pantalla.
   *
   * Hoy no alimenta el modelo de carga (docs/12 es ciego a la intensidad): se
   * acumula para poder sugerir progresión más adelante (docs/07).
   */
  import Icon from "./Icon.svelte";

  let { valor = null, sugerencias = [], guardando = false, alGuardar } = $props();

  let editando = $state(false);
  let borrador = $state("");

  function abrir() {
    borrador = valor ?? "";
    editando = true;
  }

  async function confirmar(kg) {
    const n = Number(kg);
    if (!Number.isFinite(n) || n < 0) return;
    await alGuardar(n);
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

    {#if sugerencias.length}
      <!-- Inventario del perfil: un toque en vez de teclear. -->
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
    {valor != null ? `${valor} kg` : "Apuntar peso"}
  </button>
{/if}
