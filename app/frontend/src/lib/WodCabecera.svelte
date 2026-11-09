<script>
  /** Cabecera del bloque B3 cuando va en formato WOD (docs/16): tipo, tiempo,
   *  RPE objetivo e instrucción del formato. Las estaciones son ítems normales
   *  y se renderizan debajo, como cualquier ejercicio. */
  let { wod } = $props();

  const TIPOS = { amrap: "AMRAP", emom: "EMOM", por_tiempo: "POR TIEMPO" };
</script>

{#if wod}
  <div class="mb-2 rounded-xl border border-acento/40 bg-acento/10 p-4">
    <p class="font-display text-lg font-bold tracking-wider text-acento">
      {TIPOS[wod.tipo] || wod.tipo.toUpperCase()} · {wod.minutos} MIN{#if wod.rpe_objetivo} · RPE {wod.rpe_objetivo}{/if}
    </p>
    <p class="mt-1 text-sm leading-relaxed text-apagado">{wod.descripcion}</p>
  </div>
{/if}
