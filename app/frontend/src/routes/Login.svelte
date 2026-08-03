<script>
  import { api, mensajeError } from "../lib/api.js";
  import { session } from "../lib/stores.svelte.js";
  import Icon from "../lib/Icon.svelte";

  let username = $state("");
  let password = $state("");
  let error = $state("");
  let cargando = $state(false);

  async function entrar(e) {
    e.preventDefault();
    error = "";
    cargando = true;
    try {
      const u = await api.post("/api/auth/login", { username, password });
      session.usuario = u.username;
      location.hash = "#/estado";
    } catch (e2) {
      error = mensajeError(e2);
    } finally {
      cargando = false;
    }
  }
</script>

<div class="mx-auto mt-16 max-w-sm">
  <h2 class="mb-6 flex items-center justify-center gap-2 text-center font-display text-3xl font-bold tracking-wide text-acento">
    <Icon nombre="logo" tam={30} /> FITLOSOPHY
  </h2>
  <form onsubmit={entrar} class="space-y-4">
    <input
      bind:value={username}
      type="text"
      placeholder="Usuario"
      autocomplete="username"
      required
      class="w-full rounded-xl border border-borde bg-superficie px-4 py-3 text-texto placeholder:text-tenue focus:border-acento focus:outline-none"
    />
    <input
      bind:value={password}
      type="password"
      placeholder="Contraseña"
      autocomplete="current-password"
      required
      class="w-full rounded-xl border border-borde bg-superficie px-4 py-3 text-texto placeholder:text-tenue focus:border-acento focus:outline-none"
    />
    {#if error}
      <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
        <Icon nombre="aviso" tam={16} /> {error}
      </p>
    {/if}
    <button
      type="submit"
      disabled={cargando}
      class="w-full rounded-xl bg-acento py-3 font-display text-lg font-bold tracking-wide text-fondo disabled:opacity-50"
    >
      {cargando ? "ENTRANDO…" : "ENTRAR"}
    </button>
  </form>
</div>
