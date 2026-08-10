/** Estado global con runes (Svelte 5), sin librería externa.
 *
 * `session`: usuario autenticado.
 * `flujo`: propuesta y sesión en curso entre las pantallas
 * Estado diario → Propuesta → Ejecución → Cierre.
 *
 * Vive en memoria y se pierde al recargar, así que al arrancar se repuebla
 * desde `GET /api/hoy` (`recuperado` marca que ya se intentó). Sin eso, volver
 * a abrir la aplicación a mitad de sesión dejaba en el estado diario, y
 * declararlo otra vez creaba una propuesta y una sesión nuevas: por eso
 * llegaron a convivir dos sesiones en curso el mismo día.
 */

export const session = $state({ usuario: null, verificado: false });

export const flujo = $state({
  estadoDiarioId: null,
  propuesta: null,
  sesion: null,
  recuperado: false,
  // El cierre pendiente lleva a esa pantalla al arrancar, pero se puede
  // aplazar: sin esta marca, «Hoy» rebotaba a Cierre una y otra vez.
  cierreAplazado: false,
});

export function reiniciarFlujo() {
  flujo.estadoDiarioId = null;
  flujo.propuesta = null;
  flujo.sesion = null;
  // `recuperado` no se toca: ya se consultó al servidor en este arranque.
}
