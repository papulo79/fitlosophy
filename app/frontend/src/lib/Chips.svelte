<script>
  import Icon from "./Icon.svelte";

  /** Chips on/off ≥ 40 px (spec §2).
   *  `tokens`: lista de tokens seleccionables; `marcados`: mapa token → bool (bindable);
   *  `etiquetas`: mapa token → etiqueta visible. */
  let { tokens, marcados = $bindable({}), etiquetas = {} } = $props();

  function marcarTodo(v) {
    marcados = Object.fromEntries(tokens.map((t) => [t, v]));
  }
</script>

<div>
  <div class="mb-2 flex gap-3 text-xs font-semibold">
    <button type="button" onclick={() => marcarTodo(true)} class="text-acento">Todo</button>
    <button type="button" onclick={() => marcarTodo(false)} class="text-apagado">Nada</button>
  </div>
  <div class="flex flex-wrap gap-2">
    {#each tokens as token}
      <button
        type="button"
        onclick={() => (marcados = { ...marcados, [token]: !marcados[token] })}
        class="flex min-h-10 items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-semibold transition-colors {marcados[token]
          ? 'bg-acento text-fondo'
          : 'bg-superficie text-apagado border border-borde'}"
      >
        {#if marcados[token]}<Icon nombre="check" tam={14} />{/if}
        {etiquetas[token] || token}
      </button>
    {/each}
  </div>
</div>
