/** Cliente mínimo de la API del MVP. Sesión por cookie: credentials: "include". */

export class ApiError extends Error {
  constructor(status, detail) {
    super("Error de API");
    this.status = status;
    this.detail = detail;
  }
}

async function request(method, url, body) {
  const opciones = { method, credentials: "include" };
  if (body !== undefined) {
    opciones.headers = { "Content-Type": "application/json" };
    opciones.body = JSON.stringify(body);
  }
  const resp = await fetch(url, opciones);
  let data = null;
  const texto = await resp.text();
  if (texto) {
    try {
      data = JSON.parse(texto);
    } catch {
      data = texto;
    }
  }
  if (resp.status === 401 && !url.startsWith("/api/auth/login")) {
    // Sesión caducada: volver al login.
    location.hash = "#/login";
    throw new ApiError(401, "Sesión caducada");
  }
  if (!resp.ok) {
    throw new ApiError(resp.status, data && data.detail !== undefined ? data.detail : "Error inesperado");
  }
  return data;
}

export const api = {
  get: (url) => request("GET", url),
  post: (url, body) => request("POST", url, body),
  put: (url, body) => request("PUT", url, body),
  patch: (url, body) => request("PATCH", url, body),
};

/** Mensaje legible para cualquier forma de error de la API (FastAPI usa varias). */
export function mensajeError(e) {
  const d = e?.detail;
  if (Array.isArray(d)) return d.map((x) => x.msg || JSON.stringify(x)).join("; ");
  if (d && typeof d === "object") return d.detalle || JSON.stringify(d);
  return d || e?.message || "Error inesperado";
}
