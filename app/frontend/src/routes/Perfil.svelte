<script>
  import { api, mensajeError } from "../lib/api.js";

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
</script>

<div class="space-y-4">
  <h2 class="text-xl font-bold">Perfil</h2>
  <p class="text-sm text-gray-600">
    Copia editable del perfil (misma forma que <code>data/perfil.yaml</code>). El motor la usa en cada decisión.
    {#if updatedAt}<span class="block text-xs text-gray-400">Última actualización: {updatedAt}</span>{/if}
  </p>

  <textarea bind:value={texto} rows="20" spellcheck="false" class="w-full rounded-xl border border-gray-300 p-3 font-mono text-xs"></textarea>

  {#if error}
    <p class="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>
  {/if}
  {#if mensaje}
    <p class="rounded-lg bg-green-50 p-3 text-sm text-green-700">{mensaje}</p>
  {/if}

  <button onclick={guardar} disabled={cargando} class="w-full rounded-xl bg-blue-600 py-3 font-semibold text-white disabled:opacity-50">
    {cargando ? "Guardando…" : "Guardar perfil"}
  </button>

  <a href="/api/export" download="fitlosophy-export.json" class="block rounded-xl border border-gray-300 bg-white py-3 text-center font-medium">
    Descargar copia de todos los datos (JSON)
  </a>
</div>
