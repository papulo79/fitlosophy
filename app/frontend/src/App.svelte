<script>
  import NavBar from "./lib/NavBar.svelte";
  import Icon from "./lib/Icon.svelte";
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

  // Repuebla el flujo desde el servidor tras recargar (ver stores.svelte.js).
  let recuperando = false;
  async function recuperarFlujo() {
    if (recuperando) return;
    recuperando = true;
    try {
      const hoy = await api.get("/api/hoy");
      // Una sesión sin cerrar tiene prioridad: le falta la respuesta posterior.
      flujo.sesion = hoy.sesion_activa || hoy.sesion_pendiente_cierre || null;
      if (hoy.propuesta_vigente) flujo.propuesta = hoy.propuesta_vigente;
    } catch {
      // Sin recuperación posible: se sigue con el flujo vacío.
    } finally {
      flujo.recuperado = true;
      recuperando = false;
    }
  }

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
    if (!session.usuario) {
      if (base !== "/login") location.hash = "#/login";
      return;
    }
    if (base === "/login") {
      location.hash = "#/estado";
      return;
    }
    // Hasta saber qué hay en marcha no se redirige: si no, se expulsaría de
    // Ejecución a quien acaba de recargar dentro de su sesión.
    if (!flujo.recuperado) {
      recuperarFlujo();
      return;
    }
    if (flujo.sesion?.estado === "en_curso" && base === "/estado") {
      // docs/14: reabrir a mitad de sesión devuelve a esa sesión.
      location.hash = "#/ejecucion";
    } else if (flujo.sesion?.estado === "finalizada" && base === "/estado" && !flujo.cierreAplazado) {
      // Entrenada pero sin cerrar: falta la respuesta posterior. A diferencia
      // de una sesión en curso, esto se puede aplazar: la sesión ya cuenta.
      location.hash = "#/cierre";
    } else if (base === "/propuesta" && !flujo.propuesta) {
      location.hash = "#/estado";
    } else if ((base === "/ejecucion" || base === "/cierre") && !flujo.sesion) {
      location.hash = "#/estado";
    }
  });
</script>

{#if !session.verificado}
  <p class="p-6 text-center text-apagado">Cargando…</p>
{:else}
  {#if session.usuario}
    <header class="border-b border-borde bg-superficie">
      <div class="mx-auto flex max-w-xl items-center gap-2 px-4 py-3">
        <span class="text-acento"><Icon nombre="logo" tam={22} /></span>
        <h1 class="font-display text-2xl font-bold tracking-wide text-acento">FITLOSOPHY</h1>
      </div>
    </header>
  {/if}
  <main class="mx-auto max-w-xl p-4 pb-24">
    {#key base + (parametro || "")}
      <Componente {parametro} />
    {/key}
  </main>
  {#if session.usuario}
    <NavBar />
  {/if}
{/if}
