<script>
  /** Grupo de botones grandes para elegir un valor de dominio (segmentado oscuro). */
  let { opciones, valor = $bindable(), colores = {} } = $props();
</script>

<div class="flex gap-2">
  {#each opciones as op}
    <button
      type="button"
      onclick={() => (valor = op.valor)}
      class="min-h-11 flex-1 rounded-xl border px-2 py-3 text-sm font-semibold transition-colors {valor === op.valor
        ? colores[op.valor] || 'border-acento bg-acento text-fondo'
        : 'border-borde bg-superficie text-apagado'}"
    >
      {op.etiqueta}
    </button>
  {/each}
</div>
