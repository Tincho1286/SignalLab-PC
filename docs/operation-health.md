# Operation Health

Operation Health es un ciclo de mantenimiento de SignalLab PC mediante entregas preliminares, hasta la próxima versión estable. Cada preview agrupa varias correcciones relacionadas de cálculo, transferencia de datos, importación y funcionamiento de la interfaz. La prioridad son los defectos que pueden alterar resultados o impedir continuar un trabajo.

Las notas públicas describen las mejoras aplicadas y las limitaciones conocidas. Los controles automáticos básicos forman parte de la construcción; la promoción a estable requiere además revisar el funcionamiento y resolver los problemas bloqueantes detectados durante el uso.

## Entregas del ciclo

- **1.5.6 — Operation Health 1:** filtros ideales con escalones, estado después de un fallo de presentación, diagnóstico visible y prevención de errores de nombres/importaciones en el código.
- **1.5.7 — Operation Health 2:** sinc bilateral, condiciones y unidades en CAS, posiciones no definidas en gráficos, ejes MATLAB exactos e intercambio CSV/JSON.

## Hallazgos tratados

| ID | Hallazgo | Entrega |
|---|---|---|
| OH-001 | El análisis de retardo de un filtro con step intentaba evaluar DiracDelta como un número. | 1.5.6 |
| OH-002 | Las excepciones inesperadas de acciones Qt podían dejar un botón aparentemente inactivo. | 1.5.6 |
| OH-003 | Un fallo de presentación mantenía el mensaje de cálculo en curso. | 1.5.6 |
| OH-004 | Se perdía la traza de los errores del proceso de trabajo. | 1.5.6 |
| OH-005 | Una importación local condicional podía ocultar un nombre del módulo usado en otro recorrido. | Prevención desde 1.5.6 |
| OH-006 | Una condición de convergencia deshabilitaba toda la gráfica de DTFT. | 1.5.7 |
| OH-007 | La importación MATLAB proyectaba un origen int64 a float y podía desplazar índices grandes. | 1.5.7 |
| OH-008 | DTFT → CAS → Resultados perdía la unidad de frecuencia. | 1.5.7 |
| OH-009 | Un CSV propio de eje descendente se exportaba, pero no volvía a abrirse. | 1.5.7 |
| OH-010 | Se admitían metadatos de señal de un tipo incompatible con otras herramientas. | 1.5.7 |
| OH-011 | Los archivos incompletos producían errores de claves en lugar de mensajes de validación. | 1.5.7 |
| OH-012 | La suma formal de Z de una sinc bilateral podía confundirse con un resultado simplificable. | 1.5.7 |
| OH-013 | La cancelación de un cociente en CAS podía borrar restricciones de su respuesta de frecuencia importada. | 1.5.7 |

## Continuidad hacia la estable

La revisión continúa sobre bordes, ceros y polos, escala numérica, coincidencia entre figura/tabla/exportación y recorridos entre herramientas. Los fallos de cálculo o pérdida de datos tienen prioridad sobre cambios visuales. Las previews permiten incorporar correcciones de forma gradual sin promover automáticamente una entrega a estable.

## Diagnósticos

Los errores inesperados permiten copiar una referencia, versión, plataforma, acción y traza. Los diagnósticos se guardan localmente con rotación y tamaño limitado; no se transmiten automáticamente.
