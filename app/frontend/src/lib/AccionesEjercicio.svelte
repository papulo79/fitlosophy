<script>
  /**
   * Pie de un ítem de sesión: cómo se hace el ejercicio y dónde verlo.
   *
   * Sustituye a la lupa que iba pegada al nombre. Aquella tenía dos problemas
   * en el móvil: el icono de 13 px no llega al objetivo táctil mínimo, y al
   * envolver el nombre entero en un enlace, tocar el ejercicio te sacaba de la
   * aplicación a YouTube sin haberlo pedido. Ahora el nombre es solo texto y
   * las dos acciones son botones de ancho completo y 44 px de alto.
   */
  import Icon from "./Icon.svelte";
  import { urlBusqueda } from "./busqueda.js";

  let { nombre, descripcion = "", patrones = [] } = $props();
  let desplegado = $state(false);

  const hayDetalle = $derived(Boolean(descripcion) || patrones.length > 0);
</script>

<div class="mt-3 border-t border-borde pt-2">
  <div class="flex gap-2">
    {#if hayDetalle}
      <button
        type="button"
        onclick={() => (desplegado = !desplegado)}
        aria-expanded={desplegado}
        class="flex min-h-11 flex-1 items-center justify-center gap-1.5 rounded-lg text-sm font-semibold text-apagado hover:bg-fondo hover:text-acento"
      >
        <span class="transition-transform duration-150" class:rotate-90={desplegado}>
          <Icon nombre="chevron" tam={14} />
        </span>
        Cómo se hace
      </button>
    {/if}
    <a
      href={urlBusqueda(nombre)}
      target="_blank"
      rel="noopener"
      class="flex min-h-11 flex-1 items-center justify-center gap-1.5 rounded-lg text-sm font-semibold text-apagado hover:bg-fondo hover:text-acento"
    >
      <Icon nombre="video" tam={15} /> Ver vídeo
    </a>
  </div>

  {#if desplegado}
    <div class="border-l-2 border-borde pb-1 pl-3">
      {#if descripcion}
        <p class="text-sm leading-relaxed text-apagado">{descripcion}</p>
      {/if}
      {#if patrones.length}
        <p class="mt-2 text-xs font-semibold text-tenue">Patrones</p>
        <ol class="mt-1 list-decimal space-y-1 pl-4 text-sm text-apagado marker:text-tenue">
          {#each patrones as patron}
            <li>{patron}</li>
          {/each}
        </ol>
      {/if}
    </div>
  {/if}
</div>
