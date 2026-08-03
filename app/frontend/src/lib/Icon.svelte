<script>
  /** Iconos de relleno sólido propios (spec §1). Uso: <Icon nombre="check" tam={20} /> */
  const TRAZOS = {
    hoy: "M14 3h-4l-2 8H3v2h6.6l2.4 8 4-12H21v-2h-6.6z",
    historial: "M7 2a1 1 0 0 1 1 1v1h8V3a1 1 0 1 1 2 0v1h1a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h1V3a1 1 0 0 1 1-1zm12 8H5v9h14z",
    perfil: "M12 3a5 5 0 1 1 0 10 5 5 0 0 1 0-10zm0 12c4 0 7.5 1.8 8.5 5.5a1 1 0 0 1-1 .5h-15a1 1 0 0 1-1-.5C4.5 16.8 8 15 12 15z",
    check: "M9.55 17.3 4.8 12.55l1.4-1.4 3.35 3.35 8.25-8.25 1.4 1.4z",
    aviso: "M12 3 1.5 21h21zm-1 7h2v4.5h-2zm0 6h2v2h-2z",
    mas: "M5 9.8a2.2 2.2 0 1 1 0 4.4 2.2 2.2 0 0 1 0-4.4m7 0a2.2 2.2 0 1 1 0 4.4 2.2 2.2 0 0 1 0-4.4m7 0a2.2 2.2 0 1 1 0 4.4 2.2 2.2 0 0 1 0-4.4",
    exportar: "M12 3a1 1 0 0 1 1 1v8.6l2.8-2.8a1 1 0 1 1 1.4 1.4l-4.5 4.5a1 1 0 0 1-1.4 0l-4.5-4.5a1 1 0 1 1 1.4-1.4l2.8 2.8V4a1 1 0 0 1 1-1zM5 18h14a1 1 0 1 1 0 2H5a1 1 0 1 1 0-2z",
    cerrar: "M6.4 5 5 6.4 10.6 12 5 17.6 6.4 19 12 13.4 17.6 19l1.4-1.4L13.4 12 19 6.4 17.6 5 12 10.6z",
    corregir: "M3 17.2V21h3.8L17.9 9.9l-3.8-3.8zM20.7 7.1a1 1 0 0 0 0-1.4l-2.4-2.4a1 1 0 0 0-1.4 0l-1.8 1.8 3.8 3.8z",
    atras: "M14.5 5 7.5 12l7 7 1.4-1.4-5.6-5.6 5.6-5.6z",
    plus: "M11 5h2v6h6v2h-6v6h-2v-6H5v-2h6z",
    bjj: "M12 2 8 4l-4.5 3L5 9.5l2-1V21h10V8.5l2 1 1.5-2.5L16 4zm-1 4.5 1-1.7 1 1.7-1 1.5zM9 10.5l3 4 3-4 1.2 1L13 16v4h-2v-4l-3.2-4.5z",
    logout: "M4 5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2h-2V5H6v14h6v-2h2v2a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2zm12.5 4.5L21 14l-4.5 4.5-1.4-1.4 2.1-2.1H9v-2h8.2l-2.1-2.1z",
    fisica: "M3 9a1.5 1.5 0 0 1 3 0v6a1.5 1.5 0 0 1-3 0zm4-2a1.5 1.5 0 0 1 3 0v10a1.5 1.5 0 0 1-3 0zm7 0a1.5 1.5 0 0 1 3 0v10a1.5 1.5 0 0 1-3 0zm4 2a1.5 1.5 0 0 1 3 0v6a1.5 1.5 0 0 1-3 0zM10 11h4v2h-4z",
    recuperacion: "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09A6.06 6.06 0 0 1 16.5 3C19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z",
    descanso: "M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8",
    sin_registro: "M12 4a8 8 0 1 0 8 8h-2a6 6 0 1 1-6-6z",
    // Marca del proyecto: mancuerna en diagonal (45°).
    logo: "M3 9a1.5 1.5 0 0 1 3 0v6a1.5 1.5 0 0 1-3 0zm4-2a1.5 1.5 0 0 1 3 0v10a1.5 1.5 0 0 1-3 0zm7 0a1.5 1.5 0 0 1 3 0v10a1.5 1.5 0 0 1-3 0zm4 2a1.5 1.5 0 0 1 3 0v6a1.5 1.5 0 0 1-3 0zM10 11h4v2h-4z",
  };
  const TRANSFORMS = { logo: "rotate(45 12 12)" };
  let { nombre, tam = 20 } = $props();
</script>

<svg width={tam} height={tam} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" class="shrink-0">
  <path d={TRAZOS[nombre] || TRAZOS.aviso} transform={TRANSFORMS[nombre] || ""} />
</svg>
