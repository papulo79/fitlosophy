<script>
  /**
   * Con qué intención se hace el ejercicio y con qué criterio elegir el peso
   * (docs/05). La biblioteca no prescribe kilos: el modelo de carga es ciego a
   * la intensidad, así que se declara la intención y la reserva de
   * repeticiones de la familia, y el atleta ajusta.
   */
  import { INTENCIONES } from "./etiquetas.js";

  let { intencion = "", reserva = "" } = $props();

  const info = $derived(INTENCIONES[intencion]);
</script>

{#if info || reserva}
  <p class="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
    {#if info}
      <span class="rounded-md border px-1.5 py-0.5 font-semibold {info.color}">{info.etiqueta}</span>
    {/if}
    {#if reserva}
      <span class="text-tenue">{reserva}</span>
    {/if}
  </p>
{/if}
