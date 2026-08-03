<script>
  import { api, mensajeError } from "../lib/api.js";
  import { BLOQUES, FAMILIAS, ESTADOS_ITEM, agruparPorBloque } from "../lib/etiquetas.js";
  import Opciones from "../lib/Opciones.svelte";
  import Icon from "../lib/Icon.svelte";

  let { parametro } = $props(); // fecha YYYY-MM-DD o null (lista)

  const TIPOS_DIA = {
    fisica: "Física",
    recuperacion: "Recuperación",
    bjj: "BJJ",
    descanso: "Descanso",
    sin_registro: "Sin registro",
  };
  const ICONOS_DIA = {
    fisica: "fisica",
    recuperacion: "recuperacion",
    bjj: "bjj",
    descanso: "descanso",
    sin_registro: "sin_registro",
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

  // --- Corrección de un ítem registrado (criterio 7 de docs/14) ---
  let itemCorrigiendo = $state(null); // { sesionId, item }
  let modoItem = $state("modificado");
  let formItem = $state({ series: "", repeticiones: "", segundos: "", minutos: "", carga_kg: "", exercise_id: "", motivo: "" });
  let catalogo = $state([]);
  let errorItem = $state("");

  // --- Corrección del cierre (criterio 7 de docs/14) ---
  let cierreCorrigiendo = $state(null); // id de sesión
  let cierreForm = $state({ sensacion: "como_previsto", molestias: [] });
  let errorCierre = $state("");

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

  async function abrirCorreccionItem(sesionId, item) {
    itemCorrigiendo = { sesionId, item };
    modoItem = item.estado === "pendiente" ? "completado" : item.estado;
    formItem = {
      series: item.real.series ?? "",
      repeticiones: item.real.repeticiones ?? "",
      segundos: item.real.segundos ?? "",
      minutos: item.real.minutos ?? "",
      carga_kg: item.real.carga_kg ?? "",
      exercise_id: item.exercise_id_real || "",
      motivo: item.motivo || "",
    };
    errorItem = "";
    if (catalogo.length === 0) {
      try {
        catalogo = (await api.get("/api/ejercicios")).ejercicios;
      } catch (e) {
        errorItem = mensajeError(e);
      }
    }
  }

  async function guardarCorreccionItem() {
    errorItem = "";
    const cuerpo = { estado: modoItem, motivo: formItem.motivo.trim() || null };
    if (modoItem === "sustituido") {
      if (!formItem.exercise_id) {
        errorItem = "Elige el ejercicio realizado.";
        return;
      }
      cuerpo.exercise_id_real = formItem.exercise_id;
    }
    if (modoItem === "modificado" || modoItem === "sustituido") {
      for (const [campo, clave] of [
        ["series", "series_real"],
        ["repeticiones", "repeticiones_real"],
        ["segundos", "segundos_real"],
        ["minutos", "minutos_real"],
        ["carga_kg", "carga_kg_real"],
      ]) {
        if (formItem[campo] !== "" && formItem[campo] !== null) cuerpo[clave] = Number(formItem[campo]);
      }
      if (modoItem === "modificado" && !Object.keys(cuerpo).some((k) => k.endsWith("_real"))) {
        errorItem = "Indica al menos un valor real.";
        return;
      }
    }
    try {
      // La dosis real corregida sustituye a la prevista: el backend recalcula los puntos.
      await api.put(`/api/sesiones/${itemCorrigiendo.sesionId}/items/${itemCorrigiendo.item.id}`, cuerpo);
      itemCorrigiendo = null;
      detalle = await api.get(`/api/historial/${parametro}`);
    } catch (e) {
      errorItem = mensajeError(e);
    }
  }

  function abrirCorreccionCierre(s) {
    cierreCorrigiendo = s.id;
    cierreForm = {
      sensacion: s.cierre.sensacion,
      molestias: (s.cierre.molestias || []).map((m) => ({ ...m })),
    };
    errorCierre = "";
  }

  async function guardarCorreccionCierre() {
    errorCierre = "";
    for (const m of cierreForm.molestias) {
      if (!m.zona.trim()) {
        errorCierre = "Toda molestia necesita una zona.";
        return;
      }
    }
    try {
      // Si las molestias corregidas cambian, se recalculan las ventanas congeladas (docs/12).
      await api.put(`/api/sesiones/${cierreCorrigiendo}/cierre`, {
        sensacion: cierreForm.sensacion,
        molestias: cierreForm.molestias.map((m) => ({ zona: m.zona.trim(), intensidad: Number(m.intensidad) || 0 })),
      });
      cierreCorrigiendo = null;
      detalle = await api.get(`/api/historial/${parametro}`);
    } catch (e) {
      errorCierre = mensajeError(e);
    }
  }
</script>

{#if !parametro}
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="font-display text-2xl font-bold tracking-wide">HISTORIAL (30 DÍAS)</h2>
      <button onclick={() => abrirFormBjj()} class="flex min-h-11 items-center gap-1.5 rounded-xl border border-borde bg-superficie px-3 py-2 text-sm font-semibold text-apagado">
        <Icon nombre="plus" tam={14} /> BJJ
      </button>
    </div>

    {#if errorLista}
      <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
        <Icon nombre="aviso" tam={16} /> {errorLista}
      </p>
    {/if}

    <div class="space-y-2">
      {#each dias as dia}
        <a href="#/historial/{dia.fecha}" class="block rounded-xl border border-borde bg-superficie p-4">
          <div class="flex items-center justify-between">
            <p class="font-semibold text-texto">{dia.fecha}</p>
            <div class="flex gap-2">
              {#each dia.tipos as tipo}
                <span class="flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium {tipo === 'sin_registro'
                    ? 'bg-fondo text-tenue'
                    : tipo === 'descanso'
                      ? 'bg-fondo text-apagado'
                      : 'bg-acento/15 text-acento'}">
                  <Icon nombre={ICONOS_DIA[tipo] || "sin_registro"} tam={14} />
                  {TIPOS_DIA[tipo] || tipo}
                </span>
              {/each}
            </div>
          </div>
          {#if dia.sesiones.length || dia.bjj.length}
            <p class="mt-1 text-sm text-apagado">
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
      <h2 class="font-display text-2xl font-bold tracking-wide">{parametro}</h2>
      <div class="flex gap-2">
        <button onclick={() => abrirFormBjj()} class="flex min-h-11 items-center gap-1.5 rounded-xl border border-borde bg-superficie px-3 py-2 text-sm font-semibold text-apagado">
          <Icon nombre="plus" tam={14} /> BJJ
        </button>
        <a href="#/historial" class="flex min-h-11 items-center gap-1.5 rounded-xl border border-borde bg-superficie px-3 py-2 text-sm font-semibold text-apagado">
          <Icon nombre="atras" tam={14} /> Volver
        </a>
      </div>
    </div>

    {#if errorDetalle}
      <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
        <Icon nombre="aviso" tam={16} /> {errorDetalle}
      </p>
    {/if}

    {#if detalle}
      {#if detalle.estados_diarios.length}
        <section class="rounded-xl border border-borde bg-superficie p-4 text-sm text-texto">
          <h3 class="mb-1 font-bold">Estado diario</h3>
          {#each detalle.estados_diarios as e}
            <p class="text-apagado">
              Recuperación {e.recuperacion} · dolor {e.dolor}{e.zona_dolor ? ` (${e.zona_dolor})` : ""} · BJJ: {e.bjj_disponible}{e.tipo_bjj ? ` ${e.tipo_bjj}` : ""}
              {#if e.limitacion}· limitación: {e.limitacion}{/if}
            </p>
          {/each}
        </section>
      {/if}

      {#each detalle.sesiones as s}
        <section class="rounded-xl border border-borde bg-superficie p-4">
          <div class="flex items-center justify-between">
            <h3 class="font-bold text-texto">{FAMILIAS[s.familia] || `Sesión ${s.familia}`}</h3>
            <span class="text-sm text-tenue">{ESTADOS_SESION[s.estado] || s.estado}</span>
          </div>
          <div class="mt-1 flex items-center gap-2 text-sm text-apagado">
            <span>RPE real: {s.rpe_real ?? "—"}</span>
            {#if editandoRpe === s.id}
              <input bind:value={rpeNuevo} type="number" min="1" max="10" class="w-16 rounded-lg border border-borde bg-fondo px-2 py-1 text-texto" />
              <button onclick={() => guardarRpe(s.id)} class="text-sm font-medium text-acento">Guardar</button>
              <button onclick={() => (editandoRpe = null)} class="text-sm text-tenue">Cancelar</button>
            {:else}
              <button onclick={() => { editandoRpe = s.id; rpeNuevo = s.rpe_real || 7; }} class="flex items-center gap-1 text-sm font-medium text-acento">
                <Icon nombre="corregir" tam={13} /> Corregir
              </button>
            {/if}
          </div>
          {#each agruparPorBloque(s.items) as grupo}
            <p class="mt-3 text-xs font-bold uppercase tracking-wider text-tenue">{BLOQUES[grupo.bloque] || grupo.bloque}</p>
            <ul class="mt-1 space-y-1 text-sm">
              {#each grupo.items as item}
                <li class="flex items-start justify-between gap-2">
                  <span class="min-w-0 text-texto">
                    {item.nombre}
                    <span class="block text-apagado">{item.dosis}</span>
                  </span>
                  <span class="shrink-0 text-right text-tenue">
                    {ESTADOS_ITEM[item.estado] || item.estado}
                    {#if s.estado !== "en_curso"}
                      <button onclick={() => abrirCorreccionItem(s.id, item)} class="ml-2 font-medium text-acento">Corregir</button>
                    {/if}
                  </span>
                </li>
              {/each}
            </ul>
          {/each}
          {#if s.cierre}
            <div class="mt-3 text-sm text-apagado">
              <p>
                Cierre: {s.cierre.sensacion.replace("_", " ")}
                {#if s.cierre.molestias?.length}· molestias: {s.cierre.molestias.map((m) => `${m.zona} (${m.intensidad})`).join(", ")}{/if}
                {#if s.cierre.dimensiones_congeladas?.length}· congela: {s.cierre.dimensiones_congeladas.join(", ")}{/if}
                <button onclick={() => abrirCorreccionCierre(s)} class="ml-2 inline-flex items-center gap-1 font-medium text-acento">
                  <Icon nombre="corregir" tam={13} /> Corregir
                </button>
              </p>
              {#if cierreCorrigiendo === s.id}
                <div class="mt-2 space-y-3 rounded-xl border border-borde bg-fondo p-3">
                  <Opciones
                    bind:valor={cierreForm.sensacion}
                    opciones={[
                      { valor: "como_previsto", etiqueta: "Como estaba previsto" },
                      { valor: "mas_duro", etiqueta: "Más duro" },
                      { valor: "mas_suave", etiqueta: "Más suave" },
                    ]}
                  />
                  {#each cierreForm.molestias as m, i}
                    <div class="flex gap-2">
                      <input bind:value={m.zona} type="text" placeholder="Zona (ej. lumbar)" class="flex-1 rounded-xl border border-borde bg-superficie px-3 py-2 text-texto placeholder:text-tenue" />
                      <input bind:value={m.intensidad} type="number" min="0" max="10" title="Intensidad 0-10" class="w-20 rounded-xl border border-borde bg-superficie px-3 py-2 text-texto" />
                      <button onclick={() => (cierreForm.molestias = cierreForm.molestias.filter((_, j) => j !== i))} aria-label="Quitar molestia" class="px-2 text-tenue">
                        <Icon nombre="cerrar" tam={14} />
                      </button>
                    </div>
                  {/each}
                  <button onclick={() => (cierreForm.molestias = [...cierreForm.molestias, { zona: "", intensidad: 3 }])} class="flex items-center gap-1.5 text-sm font-medium text-acento">
                    <Icon nombre="plus" tam={13} /> Añadir molestia
                  </button>
                  {#if errorCierre}
                    <p class="flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
                      <Icon nombre="aviso" tam={16} /> {errorCierre}
                    </p>
                  {/if}
                  <div class="flex gap-2">
                    <button onclick={() => (cierreCorrigiendo = null)} class="flex-1 rounded-xl border border-borde py-2 font-medium text-apagado">Cancelar</button>
                    <button onclick={guardarCorreccionCierre} class="flex-1 rounded-xl bg-acento py-2 font-semibold text-fondo">Guardar</button>
                  </div>
                </div>
              {/if}
            </div>
          {/if}
        </section>
      {/each}

      {#each detalle.propuestas as p}
        {#if !detalle.sesiones.some((s) => s.proposal_id === p.id)}
          <section class="rounded-xl border border-borde bg-superficie p-4 text-sm">
            <h3 class="font-bold text-texto">Propuesta no ejecutada ({FAMILIAS[p.familia] || p.familia})</h3>
            <p class="mt-1 text-apagado">{p.explicacion}</p>
          </section>
        {/if}
      {/each}

      {#each detalle.bjj as b}
        <section class="rounded-xl border border-borde bg-superficie p-4 text-sm">
          <div class="flex items-center justify-between">
            <h3 class="flex items-center gap-2 font-bold text-texto">
              <Icon nombre="bjj" tam={16} /> BJJ {b.clasificacion} · {b.duracion_minutos} min{b.estimado ? " (estimado)" : ""}
            </h3>
            <button onclick={() => abrirFormBjj(b)} class="flex items-center gap-1 text-sm font-medium text-acento">
              <Icon nombre="corregir" tam={13} /> Corregir
            </button>
          </div>
          <p class="mt-1 text-apagado">
            {#if b.fatiga_agarre}Fatiga de agarre · {/if}{#if b.intensidad_percibida}intensidad {b.intensidad_percibida}/10 · {/if}{b.notas || ""}
          </p>
        </section>
      {/each}

      {#if !detalle.estados_diarios.length && !detalle.sesiones.length && !detalle.bjj.length}
        <p class="text-sm text-tenue">Sin registros este día.</p>
      {/if}
    {:else if !errorDetalle}
      <p class="text-sm text-tenue">Cargando…</p>
    {/if}
  </div>
{/if}

{#if itemCorrigiendo}
  <div class="fixed inset-0 z-20 flex items-end justify-center bg-black/60" role="dialog">
    <div class="max-h-[85vh] w-full max-w-xl overflow-y-auto rounded-t-2xl bg-superficie p-5">
      <h3 class="text-lg font-bold text-texto">Corregir: {itemCorrigiendo.item.nombre}</h3>
      <p class="mb-3 text-sm text-apagado">{itemCorrigiendo.item.dosis} · el cambio recalcula la carga de los días siguientes</p>

      <div class="mb-4 grid grid-cols-2 gap-2">
        {#each [
            ["completado", "Completado tal cual"],
            ["modificado", "Completado con cambios"],
            ["sustituido", "Sustituido"],
            ["no_realizado", "No realizado"],
          ] as [valor, etiqueta]}
          <button
            onclick={() => (modoItem = valor)}
            class="min-h-11 rounded-lg border px-2 py-2 text-xs font-semibold {modoItem === valor
              ? 'border-acento bg-acento text-fondo'
              : 'border-borde bg-fondo text-apagado'}"
          >
            {etiqueta}
          </button>
        {/each}
      </div>

      <div class="space-y-3">
        {#if modoItem === "sustituido"}
          <select bind:value={formItem.exercise_id} class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto focus:border-acento focus:outline-none">
            <option value="" disabled>Ejercicio realizado…</option>
            {#each catalogo as ej}
              <option value={ej.id}>{ej.nombre}</option>
            {/each}
          </select>
        {/if}
        {#if modoItem === "modificado" || modoItem === "sustituido"}
          <div class="grid grid-cols-2 gap-2">
            <input bind:value={formItem.series} type="number" min="1" placeholder="Series" class="rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
            <input bind:value={formItem.repeticiones} type="number" min="1" placeholder="Repeticiones" class="rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
            <input bind:value={formItem.segundos} type="number" min="1" placeholder="Segundos" class="rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
            <input bind:value={formItem.minutos} type="number" min="1" placeholder="Minutos" class="rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
            <input bind:value={formItem.carga_kg} type="number" min="0" step="0.5" placeholder="Carga (kg)" class="col-span-2 rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
          </div>
        {/if}
        <input bind:value={formItem.motivo} type="text" placeholder="Motivo (opcional)" class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
      </div>

      {#if errorItem}
        <p class="mt-3 flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
          <Icon nombre="aviso" tam={16} /> {errorItem}
        </p>
      {/if}

      <div class="mt-4 flex gap-2">
        <button onclick={() => (itemCorrigiendo = null)} class="flex-1 rounded-xl border border-borde py-3 font-medium text-apagado">Cancelar</button>
        <button onclick={guardarCorreccionItem} class="flex-1 rounded-xl bg-acento py-3 font-semibold text-fondo">Guardar</button>
      </div>
    </div>
  </div>
{/if}

{#if mostrarFormBjj}
  <div class="fixed inset-0 z-20 flex items-end justify-center bg-black/60" role="dialog">
    <div class="max-h-[85vh] w-full max-w-xl overflow-y-auto rounded-t-2xl bg-superficie p-5">
      <h3 class="mb-3 text-lg font-bold text-texto">{editandoBjj ? "Corregir registro de BJJ" : "Registrar BJJ"}</h3>
      <div class="space-y-3">
        <div>
          <p class="mb-1 text-xs font-semibold uppercase tracking-wider text-tenue">Clasificación</p>
          <Opciones
            bind:valor={bjj.clasificacion}
            opciones={[
              { valor: "tecnico", etiqueta: "Técnico" },
              { valor: "normal", etiqueta: "Normal" },
              { valor: "duro", etiqueta: "Duro" },
            ]}
          />
        </div>
        <input bind:value={bjj.duracion} type="number" min="1" placeholder="Duración (minutos)" class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
        <input bind:value={bjj.fecha} type="date" class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto" />
        <label class="flex items-center gap-2 text-sm text-texto">
          <input type="checkbox" bind:checked={bjj.fatiga_agarre} class="h-5 w-5 accent-[#c8f04a]" />
          Fatiga de agarre
        </label>
        <input bind:value={bjj.intensidad} type="number" min="1" max="10" placeholder="Intensidad percibida (1-10, opcional)" class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
        <input bind:value={bjj.notas} type="text" placeholder="Notas (opcional)" class="w-full rounded-xl border border-borde bg-fondo px-3 py-3 text-texto placeholder:text-tenue" />
      </div>
      {#if errorBjj}
        <p class="mt-3 flex items-center gap-2 rounded-lg bg-rojo/10 p-3 text-sm text-rojo">
          <Icon nombre="aviso" tam={16} /> {errorBjj}
        </p>
      {/if}
      <div class="mt-4 flex gap-2">
        <button onclick={() => (mostrarFormBjj = false)} class="flex-1 rounded-xl border border-borde py-3 font-medium text-apagado">Cancelar</button>
        <button onclick={guardarBjj} class="flex-1 rounded-xl bg-acento py-3 font-semibold text-fondo">Guardar</button>
      </div>
    </div>
  </div>
{/if}
