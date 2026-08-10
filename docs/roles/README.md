# Flujo de trabajo con dos IAs

Orquestación de agentes adaptada del proyecto *Pixel Adventure: Puzzle Battles*. El desarrollo se ejecuta con dos agentes con roles separados. El orquestador es siempre OpenCode; el revisor/consultor es un CLI externo intercambiable. Cada rol existe en dos variantes — `*-kimi.md` y `*-claude.md` — idénticas salvo por el comando de invocación (`kimi --prompt` vs `claude -p "..." --dangerously-skip-permissions --model claude-opus-4-8`) y el nombre del modelo:

- **Orquestador/implementador (OpenCode):** ejecuta las tareas del plan vigente (`docs/superpowers/plans/`), una por rama, y abre un PR por tarea. Antes de pedir revisión, espera y atiende la revisión automática del bot Codex de GitHub si está activo (corrige o justifica; máx. 2 iteraciones). Sus instrucciones: `orquestador-kimi.md` o `orquestador-claude.md` (bucle autónomo, según el revisor activo) e `implementador.md` (reglas de implementación). Configuración en `opencode.json` (agentes `orquestador-kimi` y `orquestador-claude`, permisos abiertos para ejecución desatendida). Arranque: `opencode run --agent orquestador-kimi "Ejecuta el bucle del plan X"` (o `--agent orquestador-claude`).
- **Revisor (Kimi o Claude):** revisa cada PR contra el plan y los documentos de dominio, ejecuta la validación y aprueba/fusiona o pide cambios. Sus instrucciones: `revisor-kimi.md` / `revisor-claude.md`. Se invoca interactivamente ("revisa el PR #N") o en headless desde el orquestador (`kimi --prompt` / `claude -p`), terminando siempre con `VEREDICTO: APROBADO|CAMBIOS`.
- **Consultor (mismo CLI que el revisor, otro rol):** cuando el orquestador se atasca (4 intentos propios sin validación en verde), lo invoca para diagnóstico y propuesta concreta (máx. 2 intentos asistidos). Instrucciones: `consultor-kimi.md` / `consultor-claude.md`. Nunca escribe en el repo: solo propone.

## La «suite en verde» en Fitlosophy

Ya hay aplicación con tests y build, así que la validación que gobierna el bucle es:

1. **Suite del backend**: `cd app/backend && ./.venv/bin/python -m pytest` (109 tests). Incluye los 10 casos de `docs/13` como pruebas ejecutables y la integridad del catálogo.
2. **Build del frontend**: `cd app/frontend && npm run build` sin errores.
3. Coherencia entre documentos según `AGENTS.md` §Consistencia (dominios de `valores`, material ↔ `perfil.yaml`, tipos de día / semáforo / plantillas alineados, `docs/00` sincronizado).
4. Reglas de seguridad lumbar intactas.

La validación de sintaxis YAML sigue siendo obligatoria tras tocar `data/`, pero ya está cubierta por la suite: `tests/test_catalogo.py` carga el catálogo y comprueba dominios, referencias y las reglas de `docs/05`.

## Añadir ejercicios al catálogo

Para enriquecer `data/ejercicios.yaml` a partir de una transcripción de vídeo o un artículo, ver **`prompt-ejercicio-nuevo.md`**: un prompt para el agente externo y un validador determinista (`app/backend/scripts/validar_ejercicio.py`) que comprueba todo lo comprobable antes de insertar. El criterio humano se reserva a lo que lo necesita — si aporta cobertura nueva, si el impacto lumbar es correcto para este atleta y si los costes por dimensión son plausibles.

## Topes del bucle

Deterministas, definidos en `orquestador-*.md` §5: 4 intentos propios + 2 asistidos por tarea; revisión inicial + 2 rondas por PR; 2 fallos consecutivos de invocación al revisor. Cualquier condición de parada detiene el bucle con informe al usuario.

## Regla de sincronía

Las variantes `-kimi` y `-claude` de cada rol deben permanecer idénticas salvo en el comando de invocación y el nombre del modelo; cualquier cambio al bucle se aplica a ambas en el mismo commit.

## Cadencia

**Una rama = una tarea = un PR.** El plan con los checkboxes (`docs/superpowers/plans/`) es el documento vivo de seguimiento. `gh` está instalado y autenticado como `papulo79` para crear/revisar/fusionar PRs.
