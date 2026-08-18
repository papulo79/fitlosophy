# Prompt: crear la skill de OpenClaw para ejercicios candidatos

Prompt versionado para crear, en una máquina distinta, una skill local de OpenClaw que use por Telegram el proceso de candidatos de `docs/15`. El repositorio es la fuente de verdad; este prompt no autoriza al agente a modificarlo.

## Prompt

```text
Crea una skill local de OpenClaw llamada `fitlosophy-candidatos`.

Canal de uso: Telegram.
Repositorio canónico de solo lectura:
https://github.com/papulo79/fitlosophy
Rama: `main`.

Objetivo de la skill:
Analizar una fuente externa que el usuario envíe por Telegram —texto, URL,
transcripción o lista—, extraer uno o varios ejercicios explícitamente
propuestos y devolver dossiers de candidatos para Fitlosophy. La skill nunca
incorpora ejercicios directamente a la biblioteca estable.

Antes de implementar la skill:

1. Obtén una copia de solo lectura de la rama `main` del repositorio.
2. Lee completamente estos archivos:
   - AGENTS.md
   - docs/15-incorporacion-de-ejercicios-candidatos.md
   - docs/03-motor-de-decision.md
   - docs/04-gestion-de-carga.md
   - docs/05-biblioteca-de-ejercicios.md
   - docs/06-plantillas-de-sesion.md
   - docs/12-modelo-de-carga-e-inferencia.md
   - data/ejercicios.yaml
   - data/candidatos.yaml
   - docs/roles/analista-candidatos.md
   - docs/roles/revisor-candidatos.md
   - docs/roles/prompt-ejercicio-nuevo.md
3. Si el repositorio, la rama o cualquiera de esos archivos no es accesible,
   detente e informa por Telegram. No reconstruyas normas desde memoria ni
   uses fuentes alternativas sin autorización explícita.

Crea la skill siguiendo las convenciones nativas de OpenClaw. Puede escribir
solo dentro de su propio directorio local de skill. No modifiques el
repositorio clonado, no instales dependencias, no ejecutes código externo de
las fuentes y no actives automatizaciones programadas.

Guardarraíles no negociables:

1. No editar `data/ejercicios.yaml`, `data/candidatos.yaml`, código, tests,
   documentación, perfiles, historial, secretos ni configuración de Fitlosophy.
2. No crear commits, ramas, pull requests, issues, comentarios de GitHub ni
   cambios en GitHub.
3. No solicitar, recibir, almacenar ni repetir credenciales, tokens, perfiles,
   historial de entrenamiento, molestias u otros datos personales de salud.
4. La fuente demuestra únicamente que alguien propuso un ejercicio; no
   demuestra que sea seguro, apropiado o efectivo para este atleta.
5. Extraer exclusivamente ejercicios explícitos en la fuente. No inferir
   ejercicios implícitos ni proponer alternativas por iniciativa propia.
6. Si la fuente contiene varios ejercicios, crear un dossier independiente
   para cada uno.
7. Antes de investigar, deduplicar contra `data/ejercicios.yaml` por nombre,
   aliases, mecánica, patrón, material, rango y objetivo. Un nombre distinto
   no basta para considerarlo nuevo.
8. Separar de forma explícita:
   - lo que afirma la fuente;
   - evidencia adicional encontrada;
   - inferencias conservadoras del agente;
   - información no disponible.
9. Nunca inventar ejecución, dosis, limitaciones, impacto lumbar, coste por
   dimensión, compatibilidad con BJJ, material ni sustitutos.
10. Ante incertidumbre:
    - nunca proponer `impacto_lumbar: verde`;
    - nunca proponer `compatibilidad_bjj: si`;
    - no usar una dosis superior a la mínima de una alternativa estable
      comparable;
    - usar `pendiente_de_evidencia` o `descartado` cuando falte un dato crítico.
11. No declarar `candidato` válido si falta cualquiera de estos elementos:
    ejecución clara, límite de seguridad relevante, clasificación lumbar
    conservadora, coste relevante y dosis inicial prudente.
12. No autorizar pruebas experimentales ni promociones a catálogo estable.
    Solo puede recomendar que un revisor humano estudie una decisión.
13. No hacer afirmaciones de diagnóstico, tratamiento o prevención de lesiones.

Investigación:

- Para investigar un candidato, prioriza fuentes primarias, guías clínicas,
  consensos profesionales, revisiones sistemáticas o material técnico de
  organismos/profesionales identificables.
- Incluye URL y fecha de consulta de cada fuente usada.
- Si solo existe evidencia débil, contradictoria o insuficiente, indícalo;
  no rellenes la ficha para hacerla pasar.
- Si el usuario manda solo una URL de vídeo y no puedes acceder a una
  transcripción fiable, pide la transcripción o marca el análisis como
  incompleto.

La respuesta de la skill por Telegram debe tener esta estructura:

1. Resumen de entrada:
   - fuente recibida;
   - ejercicios explícitos detectados;
   - limitaciones de acceso o evidencia.

2. Un bloque por ejercicio:
   - nombre propuesto y aliases;
   - fragmento breve o referencia que prueba que aparece en la fuente;
   - deduplicación frente al catálogo estable;
   - resultado: `descartado`, `pendiente_de_evidencia` o `candidato`;
   - motivo claro de la decisión.

3. Para cada ejercicio no descartado, un bloque YAML propuesto para
   `data/candidatos.yaml`, siguiendo exactamente la plantilla de
   `docs/15-incorporacion-de-ejercicios-candidatos.md`.

4. Una tabla de evidencia con los campos:
   `ejecucion`, `limite_seguridad`, `impacto_lumbar`,
   `coste_dimensiones` y `prescripcion`.
   Cada campo solo puede ser:
   `confirmado_por_fuente`,
   `inferido_conservadoramente` o
   `no_consta`.

5. Cierre:
   - qué tendría que revisar una persona;
   - qué evidencia faltaría;
   - confirmación explícita de que ningún ejercicio ha sido añadido al catálogo
     ni autorizado para entrenamiento.

Incluye un comando de Telegram fácil de descubrir, por ejemplo:
`/candidatos <fuente o texto>`.

Al terminar de crear la skill, responde por Telegram con:
- nombre y ubicación local de la skill;
- archivos creados;
- permisos efectivos que necesita;
- un ejemplo breve de uso;
- confirmación de que no tiene permisos de escritura en GitHub.
```

## Permisos para la primera iteración

- Sin token si el repositorio es público y puede leerse por HTTPS.
- Si el repositorio es privado, token de GitHub de grano fino, limitado a este repositorio, con `Contents: Read-only` y caducidad corta.
- No otorgar permisos de escritura de contenidos, pull requests, Actions, Workflows, Secrets, Administration ni Issues.
- El token se configura como secreto del entorno de OpenClaw; nunca se copia en este prompt, mensajes de Telegram, URL ni ficheros versionados.

La creación futura de issues es una capacidad separada: requiere `Issues: Write`, confirmación explícita del usuario en Telegram y una revisión previa del flujo. No forma parte de esta primera skill.
