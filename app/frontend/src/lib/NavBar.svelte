<script>
  import Icon from "./Icon.svelte";

  const DESTINOS = [
    { ruta: "/estado", icono: "hoy", etiqueta: "Hoy" },
    { ruta: "/historial", icono: "historial", etiqueta: "Historial" },
    { ruta: "/perfil", icono: "perfil", etiqueta: "Perfil" },
  ];

  let hash = $state(location.hash);
  $effect(() => {
    const alCambiar = () => (hash = location.hash);
    window.addEventListener("hashchange", alCambiar);
    return () => window.removeEventListener("hashchange", alCambiar);
  });
  let activo = $derived("/" + (hash.replace(/^#/, "").split("/")[1] || "estado"));
</script>

<nav class="fixed inset-x-0 bottom-0 z-10 border-t border-borde bg-superficie">
  <div class="mx-auto flex max-w-xl">
    {#each DESTINOS as d}
      <a
        href="#{d.ruta}"
        class="flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-semibold {activo === d.ruta ? 'text-acento' : 'text-tenue'}"
      >
        <Icon nombre={d.icono} tam={22} />
        {d.etiqueta}
      </a>
    {/each}
  </div>
</nav>
