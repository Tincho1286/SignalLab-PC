# Mejoras de fiabilidad

El mantenimiento de SignalLab PC prioriza la exactitud de los resultados y la coherencia al trabajar entre herramientas. Las entregas preliminares reúnen correcciones relacionadas antes de incorporarse a una versión estable.

## Correcciones recientes

| Versión | Mejoras |
| --- | --- |
| [1.6.0](releases/v1.6.0.md) | Acceso uniforme a figuras e integración de las mejoras de fiabilidad de la serie 1.5. |
| [1.5.10](releases/v1.5.10-preview.md) | Respuestas de frecuencia en polos y valores extremos; validación del soporte activo de las secuencias. |
| [1.5.9](releases/v1.5.9-preview.md) | Expresiones elementales en ambos dominios, valores en bordes y condiciones de sistemas conservadas al trabajar con CAS e inversas. |
| [1.5.8](releases/v1.5.8-preview.md) | Impulsos discretos, pares de Fourier y factores de escala de Dirac en Laplace. |
| [1.5.7](releases/v1.5.7-preview.md) | DTFT de sinc bilateral, restricciones de frecuencia en CAS, posiciones no definidas y validación de archivos. |
| [1.5.6](releases/v1.5.6-preview.md) | Filtros ideales con escalones, recuperación después de errores de presentación y diagnósticos visibles. |

Cada resultado conserva su definición y sus condiciones para distinguir una expresión obtenida, una solución condicionada y un cálculo pendiente. La [documentación matemática](mathematical-reliability.md) explica los criterios de continuidad, convergencia e intercambio.

## Diagnósticos locales

Los avisos de errores inesperados permiten copiar la versión, plataforma, acción y traza del cálculo. Los archivos de diagnóstico tienen tamaño limitado y se guardan localmente; no se transmiten automáticamente.

## Áreas de mejora

La revisión continúa sobre bordes, ceros y polos, rango numérico y coincidencia entre gráficos, tablas y exportaciones. Las correcciones de cálculo y de conservación de datos tienen prioridad sobre los cambios visuales.
