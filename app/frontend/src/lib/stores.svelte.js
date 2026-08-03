/** Estado global con runes (Svelte 5), sin librería externa.
 *
 * `session`: usuario autenticado.
 * `flujo`: propuesta y sesión en curso entre las pantallas
 * Estado diario → Propuesta → Ejecución → Cierre. Si se recarga la página se
 * pierde (vive en memoria) y las pantallas redirigen al estado diario; el
 * historial permite recuperar lo ya persistido.
 */

export const session = $state({ usuario: null, verificado: false });

export const flujo = $state({
  estadoDiarioId: null,
  propuesta: null,
  sesion: null,
});

export function reiniciarFlujo() {
  flujo.estadoDiarioId = null;
  flujo.propuesta = null;
  flujo.sesion = null;
}
