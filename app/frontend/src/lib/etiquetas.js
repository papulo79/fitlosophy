/** Etiquetas legibles de los valores de dominio (docs/06). */

export const BLOQUES = {
  B0: "B0 · Calentamiento",
  B1: "B1 · Principal",
  B2: "B2 · Accesorio y core",
  B3: "B3 · Acondicionamiento",
  B4: "B4 · Vuelta a la calma",
  continuo: "Movimiento continuo",
};

export const ORDEN_BLOQUES = ["B0", "continuo", "B1", "B2", "B3", "B4"];

export const FAMILIAS = {
  A: "A · Físico compatible con BJJ",
  B: "B · Físico potente sin BJJ",
  C: "C · Recuperación activa",
  D: "D · Técnica y agilidad",
};

export const ESTADOS_ITEM = {
  pendiente: "Pendiente",
  completado: "Completado",
  modificado: "Completado con cambios",
  sustituido: "Sustituido",
  no_realizado: "No realizado",
};

/** Intención del ejercicio (docs/05): con qué criterio elegir el peso.
 *  `color` usa los tokens del tema; `nota` es la guía cuando no hay reserva. */
export const INTENCIONES = {
  fuerza: { etiqueta: "Fuerza", color: "text-acento border-acento/40 bg-acento/10" },
  potencia: { etiqueta: "Potencia", color: "text-ambar border-ambar/40 bg-ambar/10" },
  resistencia: { etiqueta: "Resistencia", color: "text-acento border-acento/40 bg-acento/10" },
  control: { etiqueta: "Control", color: "text-apagado border-borde bg-fondo" },
  coordinacion: { etiqueta: "Coordinación", color: "text-apagado border-borde bg-fondo" },
  movilidad: { etiqueta: "Movilidad", color: "text-apagado border-borde bg-fondo" },
  cardio: { etiqueta: "Cardio", color: "text-ambar border-ambar/40 bg-ambar/10" },
  recuperacion: { etiqueta: "Recuperación", color: "text-apagado border-borde bg-fondo" },
};

/** Agrupa ítems por bloque en el orden canónico. Devuelve [{bloque, items}]. */
export function agruparPorBloque(items) {
  const grupos = new Map();
  for (const item of items || []) {
    if (!grupos.has(item.bloque)) grupos.set(item.bloque, []);
    grupos.get(item.bloque).push(item);
  }
  return [...grupos.entries()]
    .sort(([a], [b]) => {
      const ia = ORDEN_BLOQUES.indexOf(a);
      const ib = ORDEN_BLOQUES.indexOf(b);
      return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
    })
    .map(([bloque, its]) => ({ bloque, items: its }));
}

/** Recuperación: texto visible; los valores de API siguen siendo verde/amarillo/rojo. */
export const RECUPERACION = {
  verde: "Bien",
  amarillo: "Regular",
  rojo: "Mal",
};
