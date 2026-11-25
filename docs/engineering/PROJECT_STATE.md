# Estado de SignalLab Engineering

**Línea base de Fase 01 cerrada con excepciones documentadas.** El trabajo de estabilización está en `develop`. El candidato auditado es `853bd67`. `main` apunta a `acb9e38`, que incorpora el código y el índice de descargas de la estable 2.0.0. La etiqueta de distribución `v2.0.0` está en `adfad5c`. [Informe de cierre](PHASE_01_CLOSEOUT.md)

| Área | Estado |
| --- | --- |
| Convención de fase | Corregida. La DFT directa de escritorio toma por defecto el índice `n` y conserva un modo con referencia a la primera muestra. Las pruebas cubren inversión, exportación y procedencia. |
| Sesiones históricas | Comprobados tres formatos de sesión, dos de proyecto y tres de diagramas. Se preservan la fase, el reloj, la ROC y las relaciones de procedencia en los casos verificados. |
| Seguridad | SBOM de los archivos nativos distribuibles con CPython 3.14.10, Expat 2.9.0 y Qt Essentials 6.12.0. OpenSSL del portable Linux vinculado a la revisión corregida de Ubuntu. Pendiente la rueda de Qt 6.12.1. |
| Validación | 821 pruebas integrales y 150 casos preventivos por sistema. Instaladores y descarga comprobados con un manifiesto de prueba. Medidos los recursos y la cancelación. La matriz visual cubre cuatro tamaños con tres escalas de Qt. |
| Arquitectura | El grafo reproduce el acoplamiento de Qt con los motores. La DFT es el único piloto propuesto al evaluar una futura extracción. [ADR 001](ADR-001-DFT-PILOT.md) |

## Dictamen de estabilización

La cobertura de Muestreo y Fourier supera el objetivo del 90 % de líneas. La cobertura global continúa por debajo del objetivo orientativo del 85 %. Las excepciones incluyen la disponibilidad de Qt 6.12.1, la UI Linux en un escritorio de uso real, el DPI del sistema y la entrega remota por el canal público.

El [informe de línea base](BASELINE_REPORT.md), la [matriz de validación](VALIDATION_MATRIX.md) y el [registro de riesgos](RISK_REGISTER.md) recogen el alcance de las verificaciones de estabilización.

## Fase 02 · Piloto DFT

El cierre técnico de Fase 01 aprobó el inicio controlado del piloto definido en ADR-001. El candidato `ce6846b` incorpora un contrato compartido por Qt, Python y CLI para la DFT directa. La IDFT y los archivos históricos conservan sus convenciones. La matriz pasó 829 pruebas y 150 casos preventivos por plataforma. Los riesgos de Fase 01 continúan en seguimiento. Esa primera autorización abarcó el piloto. [Informe del piloto](PHASE_02_DFT_PILOT.md) · [API y ejemplos](DFT_PILOT_API.md)

## Fase 02B · Engineering Core

El candidato `8ad3066` consolidó el contexto común, las cinco operaciones DSP, el flujo secuencial y el almacenamiento experimental. Pasó 850 pruebas y 150 casos preventivos por plataforma. El informe registra el alcance, cobertura, memoria estimada y las excepciones de distribución. La recomendación para Fase 03 es GO condicionado y su implementación requiere autorización específica. [Cierre de Fase 02B](phase_02b/closeout/PHASE_02B_CLOSEOUT.md)
