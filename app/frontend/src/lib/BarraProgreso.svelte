<script>
  /** «n de m» + barra de progreso en acento (spec §2). */
  let { hechos = 0, total = 0 } = $props();
  let pct = $derived(total > 0 ? Math.round((hechos / total) * 100) : 0);
</script>

<div class="flex items-center gap-3">
  <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-borde">
    <div class="h-full rounded-full bg-acento transition-all" style="width: {pct}%"></div>
  </div>
  <span class="text-sm text-apagado"><b class="text-texto">{hechos}</b> de {total}</span>
</div>
