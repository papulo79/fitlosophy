<script>
  /** Grupo de botones grandes para elegir un valor de dominio. */
  let { opciones, valor = $bindable(), colores = {} } = $props();
</script>

<div class="flex gap-2">
  {#each opciones as op}
    <button
      type="button"
      onclick={() => (valor = op.valor)}
      class="flex-1 rounded-xl border px-2 py-3 text-sm font-semibold transition-colors {valor === op.valor
        ? colores[op.valor] || 'border-blue-600 bg-blue-600 text-white'
        : 'border-gray-300 bg-white text-gray-700'}"
    >
      {op.etiqueta}
    </button>
  {/each}
</div>
