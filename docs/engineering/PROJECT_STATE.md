# Estado de SignalLab Engineering

**Fase 04 cerrada e integrada en `main` el 27 de noviembre de 2026.** La integración aprobada es `0c9e3bc`. Contiene el código del release 2.2.1 Preview, construido y validado en Windows y Ubuntu desde `08cd1bc`. Los controles posteriores al merge también aprobaron en ambos sistemas. [Expediente de cierre](phase_04/PHASE_04_CLOSEOUT.md) · [Matriz del candidato](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45923696053/attempts/2) · [Controles del merge](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45994467778)

La regresión al 200 % con escala de Qt y la conexión del portable a GitHub en Fedora 44 se verificaron. El DPI nativo de Windows al 150 % y 200 % y la revisión interactiva en Fedora Plasma se conservan como seguimiento histórico de Fase 04. La política vigente usa las pruebas específicas de escalado como evidencia diagnóstica. [Riesgos residuales de Fase 04](phase_04/RESIDUAL_RISK_REGISTER.md) · [Criterios vigentes](VALIDATION_MATRIX.md#criterios-vigentes)

La **Fase 05, Probability, Statistics & Stochastic Processes**, está autorizada y en desarrollo en `develop`. La última publicación es **2.2.1 Preview** y **2.0.0** es la LTS vigente. [Expediente de Fase 05](phase_05/README.md) · [Descargas 2.2.1](../releases/v2.2.1.md) · [Roadmap](ROADMAP.md) · [Política de distribución](RELEASE_POLICY.md)

## Línea base histórica de Fase 01

La Fase 01 cerró con excepciones documentadas sobre `853bd67`. [Informe de cierre](PHASE_01_CLOSEOUT.md)

| Área | Estado |
| --- | --- |
| Convención de fase | Corregida. La DFT directa de escritorio toma por defecto el índice `n` y conserva un modo con referencia a la primera muestra. Las pruebas cubren inversión, exportación y procedencia. |
| Sesiones históricas | Comprobados tres formatos de sesión, dos de proyecto y tres de diagramas. Se preservan la fase, el reloj, la ROC y las relaciones de procedencia en los casos verificados. |
| Seguridad | SBOM de los archivos nativos distribuibles con CPython 3.14.10, Expat 2.9.0 y Qt Essentials 6.12.0. OpenSSL del portable Linux vinculado a la revisión corregida de Ubuntu. Pendiente la rueda de Qt 6.12.1. |
| Validación | 821 pruebas integrales y 150 casos preventivos por sistema. Instaladores y descarga comprobados con un manifiesto de prueba. Medidos los recursos y la cancelación. La matriz visual cubre cuatro tamaños con tres escalas de Qt. |
| Arquitectura | El grafo reproduce el acoplamiento de Qt con los motores. La DFT es el único piloto propuesto al evaluar una futura extracción. [ADR 001](ADR-001-DFT-PILOT.md) |

## Dictamen histórico de estabilización de Fase 01

La cobertura de Muestreo y Fourier supera el objetivo del 90 % de líneas. La cobertura global continúa por debajo del objetivo orientativo del 85 %. Las excepciones incluyen la disponibilidad de Qt 6.12.1, la UI Linux en un escritorio de uso real, el DPI del sistema y la entrega remota por el canal público.

El [informe de línea base](BASELINE_REPORT.md), la [matriz de validación](VALIDATION_MATRIX.md) y el [registro de riesgos](RISK_REGISTER.md) recogen el alcance de las verificaciones de estabilización.

## Fase 02 · Piloto DFT

El cierre técnico de Fase 01 aprobó el inicio controlado del piloto definido en ADR-001. El candidato `ce6846b` incorpora un contrato compartido por Qt, Python y CLI para la DFT directa. La IDFT y los archivos históricos conservan sus convenciones. La matriz pasó 829 pruebas y 150 casos preventivos por plataforma. Los riesgos de Fase 01 continúan en seguimiento. Esa primera autorización abarcó el piloto. [Informe del piloto](PHASE_02_DFT_PILOT.md) · [API y ejemplos](DFT_PILOT_API.md)

## Fase 02B · Engineering Core

El candidato `8ad3066` consolidó el contexto común, las cinco operaciones DSP, el flujo secuencial y el almacenamiento experimental. Pasó 850 pruebas y 150 casos preventivos por plataforma. El informe registra el alcance, cobertura, memoria estimada y las excepciones de distribución. La recomendación para Fase 03 es GO condicionado y su implementación requiere autorización específica. [Cierre de Fase 02B](phase_02b/closeout/PHASE_02B_CLOSEOUT.md)

## Fase 02C · Integridad y validación del Core

El trabajo en `develop` verifica la procedencia de los cálculos y sus entradas, corrige el eje de PSD a escalas extremas y amplía los controles de entradas, cancelación y persistencia. La puerta de calidad mantiene revisiones separadas para el Core, la preparación de Fase 03 y la distribución. [Expediente y estado de cierre](phase_02c/README.md)

### Salida de 02C y consolidación para Fase 03

El escritorio guarda la hoja CAS y escribe el respaldo en segundo plano. El Core admite proyectos binarios, comparte reservas con el lector MATLAB y acredita una campaña sintética de 48 corridas. La matriz de `a80508c` alcanzó los objetivos de cobertura en Windows y Linux. E-01 se resolvió en los portables de `64dc3c4`. Las aprobaciones E-02, E-03 y E-05 delimitan el uso de MAT, la envolvente medida y el escritorio. E-04 continúa como seguimiento sin bloquear el flujo de distribución de `main`. [Dictámenes](phase_02c/validation/QUALITY_GATE_REPORT.md#cierre-técnico-de-fase-02c) · [Registro de decisiones](phase_02c/validation/EXCEPTION_APPROVAL_REGISTER.md)
