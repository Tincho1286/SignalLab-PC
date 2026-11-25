# Estado de SignalLab Engineering

**Fase 01 autorizada con condiciones.** El trabajo de estabilización está en `codex/engineering-stabilization`. La distribución vigente sigue siendo 2.0.0. Los controles del candidato de esta fase se ejecutan por SHA en la rama.

| Área | Estado |
| --- | --- |
| Convención de fase | Corregida. La DFT directa de escritorio toma por defecto el índice `n` y conserva un modo con referencia a la primera muestra. Las pruebas cubren inversión, exportación y procedencia. |
| Sesiones históricas | Comprobadas en tres formatos con los escritores originales. Se preserva fase, reloj, identidad y dependencia entre resultados. |
| Seguridad | Binarios públicos identificados. Candidato fijado en Qt Essentials 6.12.0. CPython parcheado y el inventario de versiones nativas restantes siguen abiertos. |
| Validación | El candidato `1aac793` pasó los controles de fuente y portables descartables en Windows/Linux. La evidencia distingue los estados de auditoría y distribución anteriores. |
| Arquitectura | El grafo reproduce el acoplamiento de Qt con los motores. La DFT es el único piloto propuesto al evaluar una futura extracción. [ADR 001](ADR-001-DFT-PILOT.md) |

## Dictamen de estabilización

**NO-GO para iniciar Engineering Core.** El candidato tiene una referencia reproducible, corrige el contrato de fase y conserva los datos de las sesiones históricas comprobadas. Quedan por resolver los avisos pendientes del runtime, en particular la vía verificable para actualizar CPython en Windows. La cobertura global y la de Sampling y Fourier siguen por debajo de los objetivos orientativos. También quedan abiertas la ampliación de formatos históricos comprobados y la caracterización de los límites de recursos.

El [informe de línea base](BASELINE_REPORT.md), la [matriz de validación](VALIDATION_MATRIX.md) y el [registro de riesgos](RISK_REGISTER.md) recogen el alcance de las verificaciones. El piloto DFT es una propuesta y la Fase 02 requiere autorización específica.
