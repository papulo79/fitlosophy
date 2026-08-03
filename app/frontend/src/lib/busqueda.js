// Búsqueda externa de vídeo para un ejercicio (el atleta no conoce todos los nombres).
export function urlBusqueda(nombre) {
  return `https://www.youtube.com/results?search_query=${encodeURIComponent(nombre + " ejercicio")}`;
}
