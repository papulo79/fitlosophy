<script>
  import NavBar from "./lib/NavBar.svelte";
  import Login from "./routes/Login.svelte";
  import EstadoDiario from "./routes/EstadoDiario.svelte";
  import Propuesta from "./routes/Propuesta.svelte";
  import Ejecucion from "./routes/Ejecucion.svelte";
  import Cierre from "./routes/Cierre.svelte";
  import Historial from "./routes/Historial.svelte";
  import Perfil from "./routes/Perfil.svelte";
  import { session, flujo } from "./lib/stores.svelte.js";
  import { api } from "./lib/api.js";

  // Router hash propio: en producción el servidor solo recibe "/", así que
  // basta StaticFiles(html=True) sin fallback SPA.
  const componentes = {
    "/login": Login,
    "/estado": EstadoDiario,
    "/propuesta": Propuesta,
    "/ejecucion": Ejecucion,
    "/cierre": Cierre,
    "/historial": Historial,
    "/perfil": Perfil,
  };

  let hash = $state(location.hash.replace(/^#/, "") || "/estado");

  $effect(() => {
    const alCambiar = () => {
      hash = location.hash.replace(/^#/, "") || "/estado";
    };
    window.addEventListener("hashchange", alCambiar);
    return () => window.removeEventListener("hashchange", alCambiar);
  });

  let base = $derived("/" + (hash.split("/")[1] || "estado"));
  let parametro = $derived(hash.split("/").slice(2).join("/") || null);
  let Componente = $derived(componentes[base] || EstadoDiario);

  $effect(() => {
    if (!session.verificado) {
      api
        .get("/api/auth/me")
        .then((u) => {
          session.usuario = u.username;
          session.verificado = true;
          if (location.hash.replace(/^#/, "").startsWith("/login")) location.hash = "#/estado";
        })
        .catch(() => {
          session.usuario = null;
          session.verificado = true;
          location.hash = "#/login";
        });
      return;
    }
    if (!session.usuario && base !== "/login") {
      location.hash = "#/login";
    } else if (session.usuario && base === "/login") {
      location.hash = "#/estado";
    } else if (base === "/propuesta" && !flujo.propuesta) {
      location.hash = "#/estado";
    } else if ((base === "/ejecucion" || base === "/cierre") && !flujo.sesion) {
      location.hash = "#/estado";
    }
  });
</script>

{#if !session.verificado}
  <p class="p-6 text-center text-gray-500">Cargando…</p>
{:else}
  <header class="border-b border-gray-200 bg-white">
    <div class="mx-auto max-w-xl px-4 py-3">
      <h1 class="text-lg font-bold">Fitlosophy</h1>
    </div>
  </header>
  <main class="mx-auto max-w-xl p-4 pb-20">
    {#key base + (parametro || "")}
      <Componente {parametro} />
    {/key}
  </main>
  {#if session.usuario}
    <NavBar />
  {/if}
{/if}
