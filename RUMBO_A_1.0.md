> Referencia histórica: este documento conserva el estado de su fecha. Para prioridades y evidencia vigentes, consultar [CIERRE_1.0.md](CIERRE_1.0.md) y [README.md](README.md). Algunas carencias aquí mencionadas fueron cubiertas después; no es una lista actual de bloqueos.

# SignalLab PC: consolidación hacia 1.0

Estado revisado: 24 de octubre de 2026. Esta lista no certifica calidad ni reduce el objetivo original: software portable para Sistemas y Señales I, II y Señales Aleatorias. El número de versión no representa porcentaje de avance.

## Evidencia actual

- `signallab_pc/navigation.py`: rutas disponibles de señales, operaciones, Fourier, filtros, control, muestreo, transformadas y señales aleatorias.
- `COBERTURA_SYS_II.md`: comparación con las cinco guías del usuario, con límites explícitos. Es una revisión de capacidades, no una validación de ejercicios.
- `signallab_pc/course_tools.py`, `filters.py`, `control.py`: diseño y análisis numérico; SOS en diseños digitales, con retorno a forma polinómica en algunos recorridos.
- `project.py`, `storage.py`: persistencia y formatos de intercambio. Lectura del código no demuestra recuperación correcta en uso real.
- `result_state.py`: avisos de resultados desactualizados integrados en herramientas de curso y respuesta temporal. No cubren todavía todos los paneles.
- `DESARROLLO_0.36.md`: comparación IIR implementada, pendiente de validación funcional.

## Frentes pendientes y criterio para cerrarlos

| Prioridad | Frente | Estado | Evidencia necesaria para cerrarlo |
|---|---|---|---|
| 1 | Coherencia de unidades, ejes, convenciones y normalizaciones | Parcial; revisar todos los recorridos | Cada herramienta informa dominio/unidad, origen y convención; exportación e importación los conservan |
| 1 | Corrección numérica | No validada funcionalmente | Casos de referencia de señales y sistemas continuos/discretos, transformadas, muestreo, filtros y estadística con resultados y tolerancias documentados |
| 1 | Reutilización de filtros | SOS conservado en recorridos principales; otros usan polinomios | Registro explícito de recorridos que preservan SOS, de conversiones y de límites; ausencia de cambio silencioso de representación |
| 1 | Interfaz coherente | Implementación parcial; revisión visual pendiente | Entradas locales comprensibles, funciones por partes editables, gráficos legibles, STEM discreto, textos matemáticos y avisos de estado en todos los paneles relevantes |
| 1 | Persistencia y portable | EXE generado; uso real pendiente | Guardar/reabrir sesiones y archivos sin pérdidas; ejecución en una PC sin Python; errores de archivos tratados sin perder trabajo |
| 2 | Cobertura de Sistemas y Señales I | Herramientas presentes; matriz temática pendiente | Inventario por tema con operaciones disponibles, límites y carencias, seguido de su resolución |
| 2 | Cobertura de Sistemas y Señales II | Guías revisadas; herramientas añadidas | Completar revisión de flujos combinados y validación de sus resultados; mantener límites de ROC y aproximaciones claros |
| 2 | Cobertura de Señales Aleatorias | Menú de generación, estadística y autocorrelación; PSD en Fourier | Matriz temática que incluya realizaciones/conjuntos, correlación/covarianza, estimación espectral y paso por sistemas LTI; resolver carencias detectadas |
| 2 | Ayuda y resultados reproducibles | Ayuda contextual disponible; auditoría pendiente | Cada opción explica entradas, salida, convención y limitaciones; resultados guardan parámetros suficientes para interpretarlos |
| 3 | Versión candidata | No preparada | Pendientes anteriores cerrados con evidencia; revisión completa del portable y registro de incidencias sin fallos críticos abiertos |

## Secuencia de trabajo

1. Entregar 0.36 con la comparación IIR ya implementada. Evitar incorporar más opciones aisladas durante esta entrega.
2. Revisar recorridos completos: definir señal → calcular → interpretar → reutilizar → exportar/reabrir. Corregir inconsistencias encontradas antes de ampliar esos recorridos.
3. Completar matrices temáticas de I y Aleatorias. Añadir herramientas generales cuando cubran carencias verificadas, no soluciones específicas de ejercicios.
4. Consolidar ayuda, mensajes, formatos de resultados y preservación de parámetros.
5. Preparar candidata y validar según los criterios anteriores. No llamar 1.0 a una compilación sólo porque empaqueta.

## Validación y preferencias del usuario

El usuario pidió dedicar el trabajo a mejoras y dejarle las pruebas. No se ejecutan baterías ni pruebas funcionales en esta etapa. Los pendientes de validación permanecen abiertos y no se sustituyen por inspección de código o por un empaquetado exitoso. Su cierre requiere evidencia real de uso y resultados, cuando se realice esa validación.

No hay porcentaje ni fecha de 1.0 comprometidos. Esta hoja se actualiza con evidencia y no cambia el alcance general autorizado.

## Hallazgo de consolidación: guardado al cerrar

Corregido en código para 0.37: cancelar el selector de guardado podía permitir cerrar si sólo había muestras editadas pendientes y `Project.dirty` era falso. Ahora se exige retorno exitoso de guardado y ausencia de pendientes. Validación funcional pendiente. La persistencia de formularios sin calcular y disposición de ventanas sigue abierta; se informa su exclusión actual en la interfaz.

## Consolidación: exportaciones

Implementado para 0.38 un escritor común con sustitución final para sesiones, señales JSON/CSV, transferencias y reportes HTML/TXT. La exportación CSV ya no reserva un eje completo adicional. Falta validar fallos de escritura y recuperación de los archivos en uso real; no se certifica durabilidad frente a interrupción eléctrica ni comportamiento de todos los sistemas de archivos.


## Prioridad vigente desde 0.54

Por indicación del usuario: portable validado; revisión general de UI y reutilización a su cargo; persistencia, validación general y ayuda se corrigen gradualmente. Desarrollo concentrado en cobertura de Sistemas I/II. Señales Aleatorias se pospone. Ver COBERTURA_SYS_I_II_0.54.md para avances y pendientes actuales.
