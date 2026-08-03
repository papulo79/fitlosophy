<script>
  import { api, mensajeError } from "../lib/api.js";
  import Icon from "../lib/Icon.svelte";
  import { session, reiniciarFlujo } from "../lib/stores.svelte.js";

  let texto = $state("");
  let updatedAt = $state(null);
  let mensaje = $state("");
  let error = $state("");
  let cargando = $state(false);

  $effect(() => {
    api
      .get("/api/perfil")
      .then((p) => {
        texto = JSON.stringify(p.data, null, 2);
        updatedAt = p.updated_at;
      })
      .catch((e) => (error = mensajeError(e)));
  });

  async function guardar() {
    mensaje = "";
    error = "";
    let data;
    try {
      data = JSON.parse(texto);
    } catch {
      error = "El JSON no es válido; no se ha enviado nada.";
      return;
    }
    cargando = true;
    try {
      await api.put("/api/perfil", { data });
      mensaje = "Perfil guardado.";
      const p = await api.get("/api/perfil");
      updatedAt = p.updated_at;
    } catch (e) {
      error = mensajeError(e);
    } finally {
      cargando = false;
    }
  }

  async function salir() {
    await api.post("/api/auth/logout").catch(() => {});
    session.usuario = null;
    reiniciarFlujo();
    location.hash = "#/login";
  }
</script>

<div class="space-y-4">
  <h2 class="font-display text-2xl font-bold tracking-wide">PERFIL</h2>
  <p class="text-sm text-apagado">
    Copia editable del perfil (misma forma que <code>data/perfil.yaml</code>). El motor la usa en cada decisión.
    {#if updatedAt}<span class="block text-xs text-tenue">Última actualización: {updatedAt}</span>{/if}
  </p>

  <textarea bind:value={texto} rows="20" spellcheck="false" class="w-full rounded-xl border border-borde bg-superficie p-3 font-mono text-xs text-texto"></textarea>

  {#if error}
    <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
      <Icon nombre="aviso" tam={16} /> {error}
    </p>
  {/if}
  {#if mensaje}
    <p class="flex items-center gap-2 rounded-lg bg-verde/10 p-3 text-sm text-verde">
      <Icon nombre="check" tam={16} /> {mensaje}
    </p>
  {/if}

  <button onclick={guardar} disabled={cargando} class="w-full rounded-xl bg-acento py-3 font-semibold text-fondo disabled:opacity-50">
    {cargando ? "Guardando…" : "Guardar perfil"}
  </button>

  <a href="/api/export" download="fitlosophy-export.json" class="flex items-center justify-center gap-2 rounded-xl border border-borde bg-superficie py-3 font-medium text-apagado">
    <Icon nombre="exportar" tam={16} /> Descargar copia de todos los datos (JSON)
  </a>

  <button onclick={salir} class="flex w-full items-center justify-center gap-2 rounded-xl border border-rojo/40 py-3 font-medium text-rojo">
    <Icon nombre="logout" tam={16} /> Salir
  </button>
</div>
