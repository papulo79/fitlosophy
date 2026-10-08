<script>
  /** Escala rápida 1–5 con etiqueta del valor elegido (docs/morning_state §2).
   *  `valor` es anulable: tocar el valor activo lo desmarca (registros parciales). */
  let { valor = $bindable(null), etiquetas = {} } = $props();

  const PASOS = [1, 2, 3, 4, 5];
</script>

<div>
  <div class="flex gap-2">
    {#each PASOS as paso}
      <button
        type="button"
        onclick={() => (valor = valor === paso ? null : paso)}
        class="min-h-11 flex-1 rounded-xl border font-display text-lg font-bold transition-colors {valor === paso
          ? 'border-acento bg-acento text-fondo'
          : 'border-borde bg-superficie text-apagado'}"
      >
        {paso}
      </button>
    {/each}
  </div>
  <p class="mt-1.5 min-h-4 text-xs {valor ? 'text-texto' : 'text-tenue'}">
    {valor ? etiquetas[valor] : "Sin valorar"}
  </p>
</div>
