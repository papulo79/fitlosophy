#!/usr/bin/env bash
# Despliegue de Fitlosophy en la misma máquina que sirve el túnel.
#
#   ./scripts/desplegar.sh
#
# Recompila el frontend, reinicia el servicio y comprueba que responde. Si en
# el .env hay credenciales de la API de Cloudflare, purga además el caché del
# borde: los ficheros de `assets/` llevan hash y no lo necesitan, pero el resto
# (index.html, iconos) conserva el nombre entre compilaciones.
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$RAIZ/app/backend/.env"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi
PUERTO="${FITLOSOPHY_PORT:-10012}"

echo "==> Compilando el frontend"
(cd "$RAIZ/app/frontend" && npm run build)

echo "==> Reiniciando el servicio"
systemctl --user restart fitlosophy

echo "==> Esperando a que responda en el puerto $PUERTO"
for _ in $(seq 1 30); do
  if curl -sf -o /dev/null "http://127.0.0.1:$PUERTO/"; then
    break
  fi
  sleep 1
done

if ! curl -sf -o /dev/null "http://127.0.0.1:$PUERTO/"; then
  echo "ERROR: el servicio no responde. Revisa: journalctl --user -u fitlosophy -n 50" >&2
  exit 1
fi

# Comprobación de que la política de caché sigue en su sitio: sin ella, los
# cambios tardan horas en verse a través del túnel.
CACHE="$(curl -sSI "http://127.0.0.1:$PUERTO/" | tr -d '\r' | grep -i '^cache-control:' || true)"
if [[ "$CACHE" != *"no-cache"* ]]; then
  echo "AVISO: index.html se sirve sin 'no-cache' ($CACHE)" >&2
else
  echo "==> index.html se revalida en cada carga"
fi

if [[ -n "${CLOUDFLARE_API_TOKEN:-}" && -n "${CLOUDFLARE_ZONE_ID:-}" ]]; then
  echo "==> Purgando el caché de Cloudflare"
  RESPUESTA="$(curl -sS -X POST \
    "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/purge_cache" \
    -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
    -H "Content-Type: application/json" \
    --data '{"purge_everything":true}')"
  if [[ "$RESPUESTA" == *'"success":true'* ]]; then
    echo "==> Caché purgado"
  else
    echo "AVISO: la purga falló: $RESPUESTA" >&2
  fi
else
  echo "==> Sin CLOUDFLARE_API_TOKEN/CLOUDFLARE_ZONE_ID en el .env: no se purga el caché"
fi

echo "==> Despliegue completado"
