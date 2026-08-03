<script>
  import { api, mensajeError } from "../lib/api.js";
  import { BLOQUES, FAMILIAS, ESTADOS_ITEM, agruparPorBloque } from "../lib/etiquetas.js";
  import Opciones from "../lib/Opciones.svelte";

  let { parametro } = $props(); // fecha YYYY-MM-DD o null (lista)

  const TIPOS_DIA = {
    fisica: "Física",
    recuperacion: "Recuperación",
    bjj: "BJJ",
    descanso: "Descanso",
    sin_registro: "Sin registro",
  };
  const ESTADOS_SESION = { en_curso: "En curso", finalizada: "Finalizada", cerrada: "Cerrada" };

  // --- Lista de días ---
  let dias = $state([]);
  let errorLista = $state("");

  // --- Detalle de un día ---
  let detalle = $state(null);
  let errorDetalle = $state("");

  // --- Formulario de BJJ (registrar y corregir) ---
  let mostrarFormBjj = $state(false);
  let editandoBjj = $state(null); // id del registro en edición
  let bjj = $state({ clasificacion: "normal", duracion: "", fecha: "", fatiga_agarre: false, intensidad: "", notas: "" });
  let errorBjj = $state("");

  // --- Corrección de RPE de una sesión ---
  let editandoRpe = $state(null); // id de sesión
  let rpeNuevo = $state(7);

  $effect(() => {
    if (parametro) {
      detalle = null;
      errorDetalle = "";
      api
        .get(`/api/historial/${parametro}`)
        .then((d) => (detalle = d))
        .catch((e) => (errorDetalle = mensajeError(e)));
    } else {
      dias = [];
      errorLista = "";
      api
        .get("/api/historial?dias=30")
        .then((d) => (dias = d.dias))
        .catch((e) => (errorLista = mensajeError(e)));
    }
  });

  function abrirFormBjj(registro = null) {
    if (registro) {
      editandoBjj = registro.id;
      bjj = {
        clasificacion: registro.clasificacion,
        duracion: String(registro.duracion_minutos),
        fecha: registro.fecha ? registro.fecha.slice(0, 10) : "",
        fatiga_agarre: registro.fatiga_agarre,
        intensidad: registro.intensidad_percibida ? String(registro.intensidad_percibida) : "",
        notas: registro.notas || "",
      };
    } else {
      editandoBjj = null;
      bjj = { clasificacion: "normal", duracion: "", fecha: parametro || "", fatiga_agarre: false, intensidad: "", notas: "" };
    }
    errorBjj = "";
    mostrarFormBjj = true;
  }

  async function guardarBjj() {
    errorBjj = "";
    if (!bjj.duracion) {
      errorBjj = "La duración es obligatoria.";
      return;
    }
    const cuerpo = {
      clasificacion: bjj.clasificacion,
      duracion_minutos: Number(bjj.duracion),
      fecha: bjj.fecha ? `${bjj.fecha}T12:00:00` : null,
      fatiga_agarre: bjj.fatiga_agarre,
      intensidad_percibida: bjj.intensidad ? Number(bjj.intensidad) : null,
      notas: bjj.notas.trim() || null,
    };
    try {
      if (editandoBjj) {
        await api.put(`/api/bjj/${editandoBjj}`, cuerpo);
      } else {
        await api.post("/api/bjj", cuerpo);
      }
      mostrarFormBjj = false;
      // Recargar lo visible.
      if (parametro) detalle = await api.get(`/api/historial/${parametro}`);
      else dias = (await api.get("/api/historial?dias=30")).dias;
    } catch (e) {
      errorBjj = mensajeError(e);
    }
  }

  async function guardarRpe(sesionId) {
    try {
      await api.put(`/api/sesiones/${sesionId}`, { rpe_real: rpeNuevo });
      editandoRpe = null;
      detalle = await api.get(`/api/historial/${parametro}`);
    } catch (e) {
      errorDetalle = mensajeError(e);
    }
  }
</script>

{#if !parametro}
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold">Historial (30 días)</h2>
      <button onclick={() => abrirFormBjj()} class="rounded-xl border border-gray-300 bg-white px-3 py-2 text-sm font-medium">
        + Registrar BJJ
      </button>
    </div>

    {#if errorLista}
      <p class="rounded-lg bg-red-50 p-3 text-sm text-red-700">{errorLista}</p>
    {/if}

    <div class="space-y-2">
      {#each dias as dia}
        <a href="#/historial/{dia.fecha}" class="block rounded-xl border border-gray-200 bg-white p-4">
          <div class="flex items-center justify-between">
            <p class="font-semibold">{dia.fecha}</p>
            <div class="flex gap-1">
              {#each dia.tipos as tipo}
                <span class="rounded-full px-2 py-1 text-xs font-medium {tipo === 'sin_registro'
                    ? 'bg-gray-100 text-gray-400'
                    : tipo === 'descanso'
                      ? 'bg-gray-100 text-gray-600'
                      : 'bg-blue-100 text-blue-700'}">{TIPOS_DIA[tipo] || tipo}</span>
              {/each}
            </div>
          </div>
          {#if dia.sesiones.length || dia.bjj.length}
            <p class="mt-1 text-sm text-gray-600">
              {#each dia.sesiones as s, i}{i > 0 ? " · " : ""}Sesión {s.familia} ({ESTADOS_SESION[s.estado] || s.estado}){/each}
              {#if dia.sesiones.length && dia.bjj.length} · {/if}
              {#each dia.bjj as b, i}{i > 0 ? " · " : ""}BJJ {b.clasificacion} {b.duracion_minutos} min{/each}
            </p>
          {/if}
        </a>
      {/each}
    </div>
  </div>
{:else}
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold">{parametro}</h2>
      <div class="flex gap-2">
        <button onclick={() => abrirFormBjj()} class="rounded-xl border border-gray-300 bg-white px-3 py-2 text-sm font-medium">+ BJJ</button>
        <a href="#/historial" class="rounded-xl border border-gray-300 bg-white px-3 py-2 text-sm font-medium">← Volver</a>
      </div>
    </div>

    {#if errorDetalle}
      <p class="rounded-lg bg-red-50 p-3 text-sm text-red-700">{errorDetalle}</p>
    {/if}

    {#if detalle}
      {#if detalle.estados_diarios.length}
        <section class="rounded-xl border border-gray-200 bg-white p-4 text-sm">
          <h3 class="mb-1 font-bold">Estado diario</h3>
          {#each detalle.estados_diarios as e}
            <p>
              Recuperación {e.recuperacion} · dolor {e.dolor}{e.zona_dolor ? ` (${e.zona_dolor})` : ""} · BJJ: {e.bjj_disponible}{e.tipo_bjj ? ` ${e.tipo_bjj}` : ""}
              {#if e.limitacion}· limitación: {e.limitacion}{/if}
            </p>
          {/each}
        </section>
      {/if}

      {#each detalle.sesiones as s}
        <section class="rounded-xl border border-gray-200 bg-white p-4">
          <div class="flex items-center justify-between">
            <h3 class="font-bold">{FAMILIAS[s.familia] || `Sesión ${s.familia}`}</h3>
            <span class="text-sm text-gray-500">{ESTADOS_SESION[s.estado] || s.estado}</span>
          </div>
          <div class="mt-1 flex items-center gap-2 text-sm text-gray-600">
            <span>RPE real: {s.rpe_real ?? "—"}</span>
            {#if editandoRpe === s.id}
              <input bind:value={rpeNuevo} type="number" min="1" max="10" class="w-16 rounded-lg border border-gray-300 px-2 py-1" />
              <button onclick={() => guardarRpe(s.id)} class="text-sm font-medium text-blue-600">Guardar</button>
              <button onclick={() => (editandoRpe = null)} class="text-sm text-gray-500">Cancelar</button>
            {:else}
              <button onclick={() => { editandoRpe = s.id; rpeNuevo = s.rpe_real || 7; }} class="text-sm font-medium text-blue-600">Corregir</button>
            {/if}
          </div>
          {#each agruparPorBloque(s.items) as grupo}
            <p class="mt-3 text-xs font-bold uppercase tracking-wide text-gray-400">{BLOQUES[grupo.bloque] || grupo.bloque}</p>
            <ul class="mt-1 space-y-1 text-sm">
              {#each grupo.items as item}
                <li class="flex justify-between gap-2">
                  <span>{item.nombre} — {item.dosis}</span>
                  <span class="shrink-0 text-gray-500">{ESTADOS_ITEM[item.estado] || item.estado}</span>
                </li>
              {/each}
            </ul>
          {/each}
          {#if s.cierre}
            <p class="mt-3 text-sm text-gray-600">
              Cierre: {s.cierre.sensacion.replace("_", " ")}
              {#if s.cierre.molestias?.length}· molestias: {s.cierre.molestias.map((m) => `${m.zona} (${m.intensidad})`).join(", ")}{/if}
            </p>
          {/if}
        </section>
      {/each}

      {#each detalle.propuestas as p}
        {#if !detalle.sesiones.some((s) => s.proposal_id === p.id)}
          <section class="rounded-xl border border-gray-200 bg-white p-4 text-sm">
            <h3 class="font-bold">Propuesta no ejecutada ({FAMILIAS[p.familia] || p.familia})</h3>
            <p class="mt-1 text-gray-600">{p.explicacion}</p>
          </section>
        {/if}
      {/each}

      {#each detalle.bjj as b}
        <section class="rounded-xl border border-gray-200 bg-white p-4 text-sm">
          <div class="flex items-center justify-between">
            <h3 class="font-bold">BJJ {b.clasificacion} · {b.duracion_minutos} min{b.estimado ? " (estimado)" : ""}</h3>
            <button onclick={() => abrirFormBjj(b)} class="text-sm font-medium text-blue-600">Corregir</button>
          </div>
          <p class="mt-1 text-gray-600">
            {#if b.fatiga_agarre}Fatiga de agarre · {/if}{#if b.intensidad_percibida}intensidad {b.intensidad_percibida}/10 · {/if}{b.notas || ""}
          </p>
        </section>
      {/each}

      {#if !detalle.estados_diarios.length && !detalle.sesiones.length && !detalle.bjj.length}
        <p class="text-sm text-gray-500">Sin registros este día.</p>
      {/if}
    {:else if !errorDetalle}
      <p class="text-sm text-gray-500">Cargando…</p>
    {/if}
  </div>
{/if}

{#if mostrarFormBjj}
  <div class="fixed inset-0 z-20 flex items-end justify-center bg-black/40" role="dialog">
    <div class="max-h-[85vh] w-full max-w-xl overflow-y-auto rounded-t-2xl bg-white p-5">
      <h3 class="mb-3 text-lg font-bold">{editandoBjj ? "Corregir registro de BJJ" : "Registrar BJJ"}</h3>
      <div class="space-y-3">
        <div>
          <p class="mb-1 text-sm font-semibold text-gray-600">Clasificación</p>
          <Opciones
            bind:valor={bjj.clasificacion}
            opciones={[
              { valor: "tecnico", etiqueta: "Técnico" },
              { valor: "normal", etiqueta: "Normal" },
              { valor: "duro", etiqueta: "Duro" },
            ]}
          />
        </div>
        <input bind:value={bjj.duracion} type="number" min="1" placeholder="Duración (minutos)" class="w-full rounded-xl border border-gray-300 px-3 py-3" />
        <input bind:value={bjj.fecha} type="date" class="w-full rounded-xl border border-gray-300 px-3 py-3" />
        <label class="flex items-center gap-2 text-sm">
          <input type="checkbox" bind:checked={bjj.fatiga_agarre} class="h-5 w-5" />
          Fatiga de agarre
        </label>
        <input bind:value={bjj.intensidad} type="number" min="1" max="10" placeholder="Intensidad percibida (1-10, opcional)" class="w-full rounded-xl border border-gray-300 px-3 py-3" />
        <input bind:value={bjj.notas} type="text" placeholder="Notas (opcional)" class="w-full rounded-xl border border-gray-300 px-3 py-3" />
      </div>
      {#if errorBjj}
        <p class="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700">{errorBjj}</p>
      {/if}
      <div class="mt-4 flex gap-2">
        <button onclick={() => (mostrarFormBjj = false)} class="flex-1 rounded-xl border border-gray-300 py-3 font-medium">Cancelar</button>
        <button onclick={guardarBjj} class="flex-1 rounded-xl bg-blue-600 py-3 font-semibold text-white">Guardar</button>
      </div>
    </div>
  </div>
{/if}
