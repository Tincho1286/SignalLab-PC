# Estado de SignalLab Engineering

**Fase 01 autorizada con condiciones.** El trabajo de estabilización está en `develop`. `main` apunta a `acb9e38`, que incorpora el código y el índice de descargas de la estable 2.0.0. La etiqueta de distribución `v2.0.0` sigue en `adfad5c`. Los controles del candidato se ejecutan por SHA en `develop`.

| Área | Estado |
| --- | --- |
| Convención de fase | Corregida. La DFT directa de escritorio toma por defecto el índice `n` y conserva un modo con referencia a la primera muestra. Las pruebas cubren inversión, exportación y procedencia. |
| Sesiones históricas | Comprobadas en tres formatos con los escritores originales. Se preserva fase, reloj, identidad y dependencia entre resultados. |
| Seguridad | El candidato incluye CPython 3.14.10, Expat 2.9.0 y Qt Essentials 6.12.0. Sigue abierto el inventario de versiones nativas restantes y el seguimiento de avisos posteriores. |
| Validación | `ccb6a86` pasó 814 pruebas, 150 casos preventivos y el diagnóstico de ambos portables descartables. Muestreo llegó al 92,11 % de líneas y Fourier al 91,44 %. |
| Arquitectura | El grafo reproduce el acoplamiento de Qt con los motores. La DFT es el único piloto propuesto al evaluar una futura extracción. [ADR 001](ADR-001-DFT-PILOT.md) |

## Dictamen de estabilización

**Fase 01 en estabilización.** El candidato tiene una referencia reproducible, actualiza CPython, corrige el contrato de fase y conserva los datos de las sesiones históricas comprobadas. La cobertura global sigue por debajo del objetivo orientativo. Quedan abiertos el seguimiento de dependencias nativas, la ampliación de formatos históricos comprobados y la caracterización de los límites de recursos.

El [informe de línea base](BASELINE_REPORT.md), la [matriz de validación](VALIDATION_MATRIX.md) y el [registro de riesgos](RISK_REGISTER.md) recogen el alcance de las verificaciones. El piloto DFT es una propuesta y la Fase 02 requiere autorización específica.
