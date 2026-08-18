# Diseño del MVP

## Propósito

Definir la primera aplicación útil de Fitlosophy: pantallas, flujos, qué parte del algoritmo entra y criterios de aceptación. Corresponde a la Fase 7 del roadmap (`docs/10`). La elección de stack y la construcción pertenecen a la Fase 8.

## Contexto de uso real

Cómo se usará la aplicación (declarado por el usuario):

- Dos días por semana hay BJJ en el gimnasio; el resto, entrenamiento físico diario en el gimnasio o el garaje.
- De lunes a viernes el momento de decisión es al terminar el trabajo (~16:15). En ese momento el usuario ya sabe si habrá BJJ como segunda sesión, si está cansado o si tiene tiempo para una sesión fuerte.
- Los fines de semana son más imprevistos, pero al solicitar la sesión se conocen los parámetros importantes igualmente.
- El BJJ lo declara el usuario cada día; no hay días fijos que el sistema deba asumir.
- El catálogo asume siempre el material del garaje; si la sesión se hace en el gimnasio, el usuario adapta por su cuenta (las adaptaciones se registran como modificaciones del ítem).
- La sesión propuesta se ejecuta marcando ítems; el usuario solo modifica cuando hay un motivo de peso o falta de tiempo.
- El uso termina con «Finalizar»; hasta el siguiente uso no hay interacción.

## Flujo principal

```text
Estado diario → Propuesta → Ejecución y registro → Finalizar (cierre)
                                                    ↓
                                              Historial actualizado
```

### Una sola sesión en marcha

El flujo es lineal y el día tiene un único momento de decisión, así que en cada instante existe **como mucho una sesión activa** y **una propuesta vigente** *por usuario* (ver «Acceso y privacidad»: el invariante es individual, no del despliegue):

- Con una sesión `en_curso` no se puede declarar otro estado diario ni aceptar otra propuesta: primero se finaliza o se cancela. Reabrir la aplicación a mitad de sesión debe **devolver a esa sesión**, no ofrecer empezar de cero.
- Declarar de nuevo el estado diario sin haber empezado sí está permitido —el estado real cambia a lo largo de la tarde— y **descarta** la propuesta anterior del día en lugar de acumularla.
- Una sesión se puede **cancelar** mientras está `en_curso` o `finalizada`: es la salida cuando se empieza por error, el plan se cae o se da por hecha una sesión que no fue. Una sesión cancelada no aporta carga al historial ni cuenta como estímulo de ningún patrón; cancelar una ya finalizada le retira la carga que estaba aportando, y es por tanto una corrección de registro (criterio 7). Desde `cerrada` no se cancela: el cierre pudo congelar la ventana de una dimensión y la corrección se hace por ítem desde el historial.
- El **cierre admite quedarse en lo mínimo**: la sensación es obligatoria y las molestias son opcionales. También se puede aplazar y seguir usando la aplicación; la sesión queda pendiente y se recuerda al volver a abrir.

Estados de una sesión: `en_curso` → `finalizada` → `cerrada`, o `en_curso` → `cancelada`.
Estados de una propuesta: `vigente` → `aceptada` o `descartada`.

## Pantallas y flujos

### 1. Estado diario

El cuestionario mínimo de `docs/03`. Se muestra al abrir la aplicación cuando toca decidir.

- Obligatorio: recuperación (verde/amarillo/rojo), dolor (0-10, zona si > 0), BJJ hoy (sí/no/incierto).
- Condicional: tipo de BJJ (técnico/normal/duro) si BJJ = sí o incierto.
- Opcional: limitación, sueño, tiempo disponible, preferencia, circunstancias y **material disponible hoy**: selector del inventario del garaje con marcar/desmarcar todo (por defecto, todo marcado; desmarcar todo = modo sin material para vacaciones o viajes; dejar solo el TRX = día de viaje ligero).
- Introduce: el usuario. Deriva: nada en esta pantalla.

### 2. Propuesta

Resultado del motor y el generador.

- Familia de sesión elegida y explicación (`docs/03`): reglas aplicadas, restricciones activas, carga relevante con su origen, incertidumbre declarada.
- Lista de ítems de la sesión (bloques B0-B4), cada uno con ejercicio, dosis prescrita y notas de ejecución.
- Acciones: aceptar y empezar, sustituir un ítem (reglas de `docs/06`), reducir duración.
- Introduce: nada (opcionalmente una sustitución). Deriva: familia, presupuesto, sesión completa.

### 3. Ejecución y registro

La sesión como lista de ítems marcables. Este es el corazón del registro fiel.

- **Check**: ítem completado tal cual. Es la acción por defecto y la esperada en la mayoría de ítems.
- **Menú «···» por ítem**: abre un modal para indicar qué se hizo realmente cuando no es lo prescrito:
  - Completado con cambios: series, repeticiones o carga distintas (campos numéricos).
  - Sustituido: otro ejercicio del catálogo (incluidas las adaptaciones hechas en el gimnasio).
  - No realizado: motivo opcional (sin tiempo, molestia, otro).
- RPE real de la sesión al terminar el último ítem (1-10).
- Botón **Finalizar**: cierra la ejecución y pasa al cierre.
- Introduce: lo realizado ítem a ítem y RPE real. Deriva: comparación con la propuesta, impacto real por dimensión (`docs/12` con la dosis real).

### 4. Cierre (respuesta posterior)

Tras «Finalizar», una sola pantalla breve:

- Sensación al terminar (como estaba previsto / más duro / más suave).
- Molestias durante o después (zona e intensidad, si las hay).
- Introduce: el usuario. Deriva: ajuste de carga estimada si hubo respuesta negativa (`docs/12`, congelación de ventana).

El «estado al día siguiente» no se pregunta aparte: lo captura el cuestionario del siguiente uso.

### 5. Historial

- Lista de días con sesión física, BJJ, descanso o sin registro.
- Detalle de cada día: propuesta vs. realizado, RPE previsto/real, respuesta posterior.
- Registro manual de BJJ: clasificación + duración (obligatorios), resto opcional (`docs/11`).
- Corrección de cualquier registro (portabilidad y corrección son transversales, `docs/10`).
- Introduce: registros de BJJ y correcciones. Deriva: carga activa, variables derivadas.

### 6. Perfil

- Datos básicos, objetivos y prioridades, material del garaje, restricciones permanentes o temporales.
- Edición directa sobre los datos de `data/perfil.yaml`.

## Qué parte del algoritmo entra en el MVP

Dentro:

- Cuestionario diario mínimo completo.
- Cálculo de carga activa por dimensiones con los valores provisionales de `docs/12`.
- Reglas D/C/P del motor (`docs/03`) con su orden de prioridad.
- Generador de sesiones completo (`docs/06`): composición, dosificación, sustitución, validación.
- Explicación de cada decisión.
- Recalculo con la dosis real registrada y congelación de ventana tras respuesta negativa.

Fuera (post-MVP, roadmap fases 9-12):

- Calibración automática de valores (se ajustan a mano tras revisar el historial).
- Aprendizaje individual y detección de patrones asociados a molestias.
- Integraciones con wearables, calendario o peso.
- Panel de carga por dimensiones y vistas semanales/mensuales.
- Soporte de material por ubicación (gimnasio vs garaje): el usuario adapta manualmente.
- Días fijos de BJJ: el usuario lo declara cada día.

## Persistencia y portabilidad

- Datos locales, exportables en formato abierto y comprensible (JSON o YAML).
- El usuario puede corregir cualquier registro.
- La aplicación no oculta incertidumbre ni inventa datos: los valores estimados se muestran como estimados.

## Acceso y privacidad

- Aplicación privada de **uso familiar**: varios atletas comparten el despliegue, cada uno con su usuario y contraseña. El acceso está protegido; sin sesión válida no se consulta ni se registra nada.
- **Cada usuario es un sistema independiente.** Su perfil, su estado diario, sus propuestas, sus sesiones, su BJJ y su historial son suyos. La carga activa se calcula solo con sus propios eventos: los entrenamientos de otro usuario no reducen ni condicionan la sesión de nadie. Los invariantes del flujo (una sesión activa, una propuesta vigente) son individuales.
- **No hay registro, ni roles, ni gestión de cuentas desde la aplicación.** Las altas y las contraseñas se administran a mano en el servidor, por línea de órdenes. La API no expone ninguna operación de gestión de usuarios: es la superficie que no existe la que no se puede atacar.
- Un recurso que no es tuyo **no existe para ti**: se responde 404, no 403. Un 403 confirmaría que ese identificador pertenece a alguien.
- Los datos son personales de salud y rendimiento: no se comparten con terceros —tampoco entre usuarios del mismo despliegue— y el despliegue es privado (local o servidor propio).
- El material del catálogo es el del lugar de entrenamiento y se comparte; lo personal (medidas, objetivos, fuerza, movilidad, consideraciones) es de cada uno y se edita desde su pantalla de perfil.
- Sesión persistente razonable: no pedir credenciales en cada uso diario, pero sí proteger el acceso desde dispositivos nuevos.

## Criterios de aceptación funcionales

El MVP es aceptable cuando:

1. Los 10 casos de `docs/13` se reproducen como pruebas funcionales: mismo estado e historial → misma familia, mismos patrones restringidos y explicación equivalente.
2. El flujo completo funciona de extremo a extremo: estado diario → propuesta → ejecución con marcado → Finalizar → cierre → historial actualizado.
3. Marcar un ítem con check requiere una sola acción; modificarlo, abrir el modal y cubrir solo lo que cambió.
4. Una modificación registrada cambia la carga calculada de los días siguientes (la dosis real sustituye a la prevista).
5. Una respuesta negativa en el cierre congela la ventana de la dimensión afectada (`docs/12`).
6. Toda propuesta muestra su explicación con reglas citadas e incertidumbre declarada.
7. Los datos pueden exportarse y cualquier registro puede corregirse.
8. Ninguna regla dura puede saltarse desde la interfaz: las sustituciones que la violan se rechazan con su motivo.
9. El acceso exige usuario y contraseña; sin sesión válida no se puede consultar ni registrar nada.
10. **Ningún usuario puede leer ni modificar datos de otro.** Con la sesión de A, ningún identificador de un recurso de B es accesible (404), el historial y la carga activa de A se calculan solo con sus eventos, la exportación de A contiene solo lo suyo, y lo que A haga —empezar una sesión, redeclarar su estado diario— no altera el flujo de B.

## Decisiones tomadas en esta fase

- Material: garaje completo por defecto; el estado diario permite seleccionar el material disponible (marcar/desmarcar todo incluido). Adaptaciones en el gimnasio se registran como sustituciones del ítem.
- BJJ: declarado cada día por el usuario; el sistema no asume días fijos.
- Marcado: check = tal cual; modal para cualquier desviación; la modificación es la excepción, no la norma.
- Cierre: «Finalizar» dispara la respuesta posterior y termina el uso hasta el siguiente día.
- Acceso: aplicación privada de uso familiar. Varios usuarios con usuario y contraseña, aislados entre sí; sin registro ni gestión de cuentas por HTTP. Las altas y las rotaciones de contraseña se hacen por línea de órdenes en el servidor.
- Perfil de un usuario nuevo: se siembra desde una plantilla con el material del lugar de entrenamiento —compartido— y el resto de secciones vacías, para que cada uno las rellene. El perfil de un atleta nunca se copia a otro.
