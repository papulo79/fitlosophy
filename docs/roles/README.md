# Flujo de trabajo con dos IAs

Orquestación de agentes adaptada del proyecto *Pixel Adventure: Puzzle Battles*. El desarrollo se ejecuta con dos agentes con roles separados. El orquestador es siempre OpenCode; el revisor/consultor es un CLI externo intercambiable. Cada rol existe en dos variantes — `*-kimi.md` y `*-claude.md` — idénticas salvo por el comando de invocación (`kimi --prompt` vs `claude -p "..." --dangerously-skip-permissions --model claude-opus-4-8`) y el nombre del modelo:

- **Orquestador/implementador (OpenCode):** ejecuta las tareas del plan vigente (`docs/superpowers/plans/`), una por rama, y abre un PR por tarea. Antes de pedir revisión, espera y atiende la revisión automática del bot Codex de GitHub si está activo (corrige o justifica; máx. 2 iteraciones). Sus instrucciones: `orquestador-kimi.md` o `orquestador-claude.md` (bucle autónomo, según el revisor activo) e `implementador.md` (reglas de implementación). Configuración en `opencode.json` (agentes `orquestador-kimi` y `orquestador-claude`, permisos abiertos para ejecución desatendida). Arranque: `opencode run --agent orquestador-kimi "Ejecuta el bucle del plan X"` (o `--agent orquestador-claude`).
- **Revisor (Kimi o Claude):** revisa cada PR contra el plan y los documentos de dominio, ejecuta la validación y aprueba/fusiona o pide cambios. Sus instrucciones: `revisor-kimi.md` / `revisor-claude.md`. Se invoca interactivamente ("revisa el PR #N") o en headless desde el orquestador (`kimi --prompt` / `claude -p`), terminando siempre con `VEREDICTO: APROBADO|CAMBIOS`.
- **Consultor (mismo CLI que el revisor, otro rol):** cuando el orquestador se atasca (4 intentos propios sin validación en verde), lo invoca para diagnóstico y propuesta concreta (máx. 2 intentos asistidos). Instrucciones: `consultor-kimi.md` / `consultor-claude.md`. Nunca escribe en el repo: solo propone.

## La «suite en verde» en Fitlosophy

Como no hay tests ni build, la validación que gobierna el bucle es:

1. Sintaxis YAML válida si se tocó `data/`:
   `python3 -c "import yaml; [yaml.safe_load(open(f)) for f in ['data/perfil.yaml','data/ejercicios.yaml']]"`
2. Coherencia entre documentos según `AGENTS.md` §Consistencia (dominios de `valores`, material ↔ `perfil.yaml`, tipos de día / semáforo / plantillas alineados, `docs/00` sincronizado).
3. Reglas de seguridad lumbar intactas.

Si en el futuro se añade una app con tests, esa suite pasa a ser la validación principal y estos archivos deben actualizarse.

## Topes del bucle

Deterministas, definidos en `orquestador-*.md` §5: 4 intentos propios + 2 asistidos por tarea; revisión inicial + 2 rondas por PR; 2 fallos consecutivos de invocación al revisor. Cualquier condición de parada detiene el bucle con informe al usuario.

## Regla de sincronía

Las variantes `-kimi` y `-claude` de cada rol deben permanecer idénticas salvo en el comando de invocación y el nombre del modelo; cualquier cambio al bucle se aplica a ambas en el mismo commit.

## Cadencia

**Una rama = una tarea = un PR.** El plan con los checkboxes (`docs/superpowers/plans/`) es el documento vivo de seguimiento. `gh` está instalado y autenticado como `papulo79` para crear/revisar/fusionar PRs.
