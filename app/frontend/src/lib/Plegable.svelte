<script>
  /**
   * Bloque plegable con cabecera pulsable.
   *
   * La cabecera es el objetivo táctil (≥ 44 px, spec de usabilidad móvil): en
   * el móvil un texto pequeño con un icono de 12 px no se acierta.
   *
   * Uso:
   *   <Plegable titulo="Cómo se hace">contenido</Plegable>
   */
  import Icon from "./Icon.svelte";

  let { titulo, abierto = false, children } = $props();
  let desplegado = $state(abierto);
</script>

<div>
  <button
    type="button"
    onclick={() => (desplegado = !desplegado)}
    aria-expanded={desplegado}
    class="flex min-h-11 w-full items-center gap-2 rounded-lg px-1 text-left text-sm font-semibold text-apagado hover:text-acento"
  >
    <span class="transition-transform duration-150" class:rotate-90={desplegado}>
      <Icon nombre="chevron" tam={14} />
    </span>
    {titulo}
  </button>

  {#if desplegado}
    <div class="border-l-2 border-borde pb-1 pl-3">
      {@render children()}
    </div>
  {/if}
</div>
