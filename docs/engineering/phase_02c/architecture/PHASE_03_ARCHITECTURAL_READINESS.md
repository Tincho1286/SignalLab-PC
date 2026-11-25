# Preparación técnica evaluada

| Necesidad | Base disponible | Condición antes de ampliar |
| --- | --- | --- |
| I/Q y relojes | `complex128`, reloj, unidades, DFT/IDFT y conversión racional | Preservar la escala y el origen en cada contrato nuevo |
| Conformación y filtrado adaptado | Secuencias, FIR y convolución con oráculos | Definir convenciones y ensayos por operación |
| Experimentos reproducibles | Entradas, contexto, publicación conjunta y procedencia | Definir semillas y parámetros como evidencia de cada experimento |
| Estadísticas | Potencia, PSD y operaciones sobre registros | Establecer unidades, validación y un presupuesto por perfil |
| Persistencia y volumen | JSON, SLBIN individual y benchmarks | Mantener la envolvente medida y volver a evaluar proyectos grandes |

La evaluación es de capacidad del Core. Cualquier implementación de Fase 03 requiere un alcance autorizado y un dictamen de salida.
