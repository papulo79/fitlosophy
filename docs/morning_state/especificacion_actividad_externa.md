# Especificación funcional — Registro de actividad externa

**Versión:** 1.0  
**Módulo:** Historial de entrenamientos  
**Funcionalidad:** Registrar actividad externa  
**Alcance:** Funcional; sin decisiones sobre modelos de datos, arquitectura ni tecnologías.

## 1. Objetivo

Permitir registrar **sesiones deportivas realizadas fuera del generador de entrenamientos** (especialmente BJJ y grappling), para disponer de un historial completo de la actividad y estimar la carga total de entrenamiento.

Esta funcionalidad será **independiente de «Estado diario»**: el Estado diario recoge bienestar y recuperación al levantarse; el registro de actividad externa documenta el esfuerzo realizado en una sesión.

En esta versión los registros serán informativos: **no modificarán automáticamente** las sesiones propuestas por el generador.

## 2. Ubicación y acceso

- Incorporar la acción **«Registrar actividad externa»** en el apartado **Historial de entrenamientos**.
- Las actividades externas deberán aparecer en el historial cronológico junto a los entrenamientos generados por la aplicación, identificadas claramente como **«Actividad externa»**.
- Se podrán consultar, editar y eliminar, con confirmación antes de eliminar.
- Se permitirá registrar varias actividades externas el mismo día, incluso si ese día existe un entrenamiento generado.

## 3. Formulario de registro

| Nombre visible | Descripción / valores | Obligatorio |
|---|---|---|
| **Fecha** | Fecha de realización. Por defecto, hoy; editable. | Sí |
| **Actividad** | Selector: **BJJ**, **Grappling**, **Otra**. | Sí |
| **Duración (minutos)** | Duración total de la sesión, incluyendo las pausas habituales dentro de ella; número entero mayor que cero. | Sí |
| **Esfuerzo percibido (RPE)** | Escala de **1 a 10**, valoración global de toda la sesión. | Sí |
| **Número de combates** | Número entero ≥ 0; útil para sesiones de BJJ/grappling. | No |
| **Observaciones** | Texto libre breve para detalles relevantes (p. ej., «mucho trabajo de suelo»). | No |

Si se selecciona **«Otra»**, permitir indicar el **nombre de la actividad** en un campo adicional obligatorio.

### Escala de esfuerzo percibido (RPE)

Mostrar una ayuda breve para dar consistencia a los registros:

| RPE | Etiqueta orientativa |
|---|---|
| 1–2 | Muy suave |
| 3–4 | Suave |
| 5–6 | Moderado |
| 7–8 | Intenso |
| 9 | Muy intenso |
| 10 | Máximo esfuerzo |

**Instrucción visible:** «Valora el esfuerzo global de la sesión, no solo su parte más intensa. Regístralo preferentemente poco después de terminar».

## 4. Comportamiento funcional

1. El usuario abre **Historial de entrenamientos → Registrar actividad externa**.
2. Completa los campos obligatorios y, si quiere, los opcionales.
3. Guarda la actividad y esta aparece inmediatamente en el historial del día correspondiente.
4. Desde el historial puede consultar el detalle, corregir datos o eliminar el registro.
5. El registro **no requiere** que exista una sesión generada ni un Estado diario para esa fecha.
6. Los campos opcionales vacíos permanecerán como no informados; no se interpretarán automáticamente como cero, salvo que el usuario introduzca explícitamente el valor 0 en «Número de combates».

## 5. Consulta e indicadores

En el listado mostrar, como mínimo, **fecha · actividad · duración · RPE**, y la etiqueta **«Actividad externa»**.

En el detalle mostrar también número de combates y observaciones cuando existan.

Para facilitar análisis posteriores, calcular una **carga interna orientativa**:

**Carga de sesión = duración total en minutos × RPE global**

- Expresar el resultado en **unidades arbitrarias (UA)**, sin presentarlo como calorías ni como una medida fisiológica exacta.
- Ejemplo: **BJJ · 60 min · RPE 7 → 420 UA**.
- Cuando se muestren agregados diarios o semanales, distinguir las actividades externas y los entrenamientos generados. Solo sumar cargas de sesiones que dispongan de datos comparables; no convertir duraciones estimadas en duraciones reales.
- La carga calculada no genera ajustes automáticos en esta versión.

## 6. Fuera de alcance (v1.0)

- Registro de cada combate individual.
- Frecuencia cardíaca, GPS, calorías o integración con relojes.
- Cronómetro o registro en tiempo real.
- Cuestionarios de recuperación o sueño (pertenecen a **Estado diario**).
- Modificación automática del generador según la actividad externa.
- Planificación de actividades externas futuras.

## 7. Requisitos funcionales

| ID | Requisito | Prioridad |
|---|---|---|
| AE-01 | Acceso a «Registrar actividad externa» desde Historial de entrenamientos | Alta |
| AE-02 | Registro de fecha, actividad, duración y RPE | Alta |
| AE-03 | Actividades BJJ, Grappling y Otra (con nombre si se usa Otra) | Alta |
| AE-04 | Número de combates y observaciones opcionales | Media |
| AE-05 | Mostrar actividad externa en el historial, diferenciada de sesiones generadas | Alta |
| AE-06 | Consultar, editar y eliminar registros | Alta |
| AE-07 | Permitir varios registros en un mismo día | Alta |
| AE-08 | Calcular y mostrar carga orientativa en UA | Media |
| AE-09 | Mantener el registro independiente de Estado diario y del generador | Alta |
| AE-10 | No alterar automáticamente los entrenamientos en v1.0 | Alta |

## 8. Criterios de aceptación

- Es posible registrar **«BJJ · 60 min · RPE 7 · 5 combates»** en una fecha concreta, sin crear un entrenamiento generado.
- El historial muestra esa sesión con la etiqueta **«Actividad externa»** y permite acceder a su detalle.
- La carga orientativa del ejemplo se muestra como **420 UA**.
- Es posible registrar dos actividades externas en el mismo día y mantener además un entrenamiento generado.
- Es posible editar duración y RPE y ver actualizada la carga calculada.
- Es posible eliminar una entrada tras confirmación.
- No se puede guardar una actividad sin fecha, tipo, duración positiva o RPE válido.
- Si se elige «Otra», se solicita el nombre de la actividad.
- Guardar una actividad externa no modifica automáticamente el plan de entrenamiento ni el registro de Estado diario.

---

**Resultado esperado:** un registro manual, rápido y coherente con el historial actual que permita contabilizar el trabajo de BJJ y grappling sin llevar dispositivos durante el contacto físico.
