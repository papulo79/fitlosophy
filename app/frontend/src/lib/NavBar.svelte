<script>
  import { session, reiniciarFlujo } from "./stores.svelte.js";
  import { api } from "./api.js";

  async function salir() {
    await api.post("/api/auth/logout").catch(() => {});
    session.usuario = null;
    reiniciarFlujo();
    location.hash = "#/login";
  }
</script>

<nav class="fixed inset-x-0 bottom-0 z-10 border-t border-gray-200 bg-white">
  <div class="mx-auto flex max-w-xl">
    <a href="#/estado" class="flex-1 py-3 text-center text-sm font-medium">Hoy</a>
    <a href="#/historial" class="flex-1 py-3 text-center text-sm font-medium">Historial</a>
    <a href="#/perfil" class="flex-1 py-3 text-center text-sm font-medium">Perfil</a>
    <button onclick={salir} class="flex-1 py-3 text-center text-sm font-medium text-red-600">Salir</button>
  </div>
</nav>
