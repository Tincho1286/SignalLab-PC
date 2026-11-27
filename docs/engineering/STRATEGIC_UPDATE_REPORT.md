# Informe de actualización estratégica de SignalLab Engineering

**Fecha de la revisión:** 27 de noviembre de 2026.

**Alcance:** auditoría del estado actual, roadmap, políticas y plan documental de modernización en `develop`.

## Estado comprobado

| Referencia | Estado al iniciar la auditoría |
| --- | --- |
| Ramas oficiales | GitHub tenía solo `main` y `develop`. Ambas apuntaban a `0c9e3bcdafd89dfd4437b28a93f0606fa5116542` y los dos worktrees estaban limpios. |
| Fase 04 | Cierre aprobado e integrado en `main`. Aprobó la matriz del candidato y los controles postintegración en Windows y Ubuntu. |
| Última publicación | 2.2.1 Preview, etiqueta `v2.2.1` y SHA de construcción `08cd1bc28189ef0c1cd6c5a36f2d9bd32f6f1a48`. |
| Stable/LTS | 2.0.0 sigue siendo la última estable. La etiqueta `v2.0.0` resuelve a `adfad5c093a236b0565f00f5e97845acf040ec96`. |
| Continuidad | La Fase 05 espera autorización de inicio. El ejercicio actualiza documentos y conserva el estado técnico de producto y los expedientes históricos. |

El clon conserva trece referencias locales de trabajos anteriores, once `release/1.8.x` y dos `codex/*`. Ninguna aparece como rama oficial en GitHub ni en un worktree activo. Su limpieza queda fuera del alcance de esta actualización. [Auditoría de distribución](DISTRIBUTION_INFRASTRUCTURE_AUDIT.md)

La verificación consultó las referencias remotas, la lista de Releases y la ejecución de GitHub del merge. La evidencia de escritorio mantiene su alcance registrado. La observación al 200 % usó escalado de Qt. La prueba Fedora 44 verificó conexión y manifiestos desde el portable. Las comprobaciones nativas de Windows a 150 % y 200 % y el uso interactivo en Fedora Plasma permanecen como seguimiento de Fase 04. [Cierre de Fase 04](phase_04/PHASE_04_CLOSEOUT.md) · [Controles postintegración](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45994467778) · [Preview publicada](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.2.1) · [LTS publicada](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.0.0)

## Roadmap anterior y nuevo

| Fase | Plan anterior | Dirección oficial | Familia |
| --- | --- | --- | --- |
| 00 y 01 | Auditoría y estabilización | Engineering Audit y Stabilization, con expedientes preservados | Histórica |
| 02A, 02B y 02C | Core con piloto 02 y expedientes 02B y 02C | Engineering Core Pilot, Engineering Core Consolidation y Core Hardening & Quality Gate | Histórica |
| 03 | Comunicaciones | Digital Communications Lab, cerrado | 2.1.x |
| 04 | Canales | Channel Modeling, cerrado | 2.2.x |
| 05 | SDR y espectro | Probability, Statistics & Stochastic Processes | 2.3.x |
| 06 | RF | RF & Microwave, analítica y modernización de filtros y espectros | 2.4.x |
| 07 | Punto fijo y FPGA | Fixed-Point & Embedded DSP, modernización de precisión, filtros y conversión | 2.5.x |
| 08 | Simulación de sistemas | System Simulation & Numerical Engineering, con sistemas, CAS y transformadas | 2.6.x |
| 09 | Plataforma con plugins, dispositivos e instrumentos | Integrated Engineering Platform, centrada en proyectos, flujos y ergonomía | 2.7.x |
| 10 | Consolidación final | SDR & Experimental Engineering, última expansión funcional | 2.8.x |
| 11 | Sin fase numerada | Final Engineering Consolidation & Qualification | Por determinar |

El plan anterior permanece disponible por SHA. La Fase 02A identifica el piloto que el expediente de su época llamó Fase 02. Las menciones a Fase 10 como consolidación en el cierre de Fase 03 registran lo que se planificaba entonces. [Roadmap anterior](https://github.com/Tincho1286/SignalLab-PC/blob/0c9e3bcdafd89dfd4437b28a93f0606fa5116542/docs/engineering/ROADMAP.md) · [Roadmap vigente](ROADMAP.md) · [Referencia histórica](phase_03/PHASE_03_CLOSEOUT.md)

## Cambios de política

- **Dos ejes por fase.** Además de ampliar el dominio, auditar y modernizar herramientas relacionadas, integrar servicios con Engineering Core y comprobar regresiones con oráculos y casos de uso. La planificación queda sujeta a alcance verificable y autorización de inicio.
- **Workbench incremental.** Reutilizar familias, variantes, búsqueda y ayuda. Mostrar entradas esenciales y controles contextuales sin ocultar unidades, supuestos ni condiciones científicas. Fase 05 será el piloto de este patrón cuando se autorice. [Diseño del Workbench](UX_DESIGN_PRINCIPLES.md)
- **Calificación, aceptación e integración.** Gate A habilita publicar Preview de una fase autorizada con matriz del mismo SHA, archivos y firma verificados. Gate B registra la aceptación funcional del propietario y permite ciclos de corrección. Gate C exige su autorización explícita para integrar y cerrar. [Política de entregas](RELEASE_POLICY.md)
- **Pruebas de interfaz.** DPI específico y escritorios manuales pasan a diagnóstico. Se mantienen los controles funcionales automatizados en ambos sistemas y el tratamiento de regresiones y defectos conocidos. [Criterios de validación](VALIDATION_MATRIX.md#criterios-vigentes)
- **Calidad científica y cobertura.** Expansión conserva 85 % de líneas y 75 % de ramas globales, 90 % de líneas y 85 % de ramas críticas y cero P0 o P1 internos pendientes. Fase 11 concentra los cinco umbrales de 99 % y los dictámenes técnicos y científicos independientes. [Calificación definitiva](ROADMAP.md#fase-11--consolidación-y-calificación-definitiva)
- **LTS y seguridad.** Stable/LTS 2.0.x conserva etiquetas, artefactos y mantenimiento en HEAD desacoplado. La autorización permanente cubre solo Preview calificadas de fases autorizadas. Las claves, los controles de firma, los tags históricos y la decisión sobre riesgos conservan su protección. [Ramas, firma y canales](RELEASE_POLICY.md)

## Inventario, reutilización y duplicaciones

La consulta del catálogo registró 45 entradas en 8 áreas y 99 rutas de catálogo. Se distinguieron las 124 rutas de Workbench y el CAS transversal. El inventario revisó generadores y medidas de señales, LTI y diagramas, filtros, Fourier, muestreo, Laplace/Z y CAS, aleatorias, comunicación/canales y persistencia. [Inventario preliminar](TOOL_MODERNIZATION_PLAN.md#inventario-de-partida)

| Fase | Solapamiento comprobado | Modernización prevista |
| --- | --- | --- |
| 05 | Realizaciones normal/uniforme/Bernoulli, auto/correlación cruzada, AR por Yule–Walker y OLS, AIC/AICc/BIC, pronóstico, Welch/periodograma/PSD AR. Los canales ya usan AWGN, Rayleigh/Rician, fase Wiener, réplicas e intervalos de error. | Extender realizaciones, estadísticas, correlación, modelos y PSD. Generalizar únicamente las primitivas de canal y campañas con hipótesis compatibles. |
| 06 | Respuesta y retardo de grupo, filtros analógicos y RC, picos espectrales con interpolación, ENBW y ganancia coherente. Existe Zoom FFT interno para Clarke y pérdidas de propagación analíticas. | Integrar variantes espectrales y de filtros en las herramientas existentes, y crear un contrato distinto para redes RF. |
| 07 | Q, saturación, wraparound, acumulador, SOS, sensibilidad, ciclos límite, conversión racional polifásica y notch biquad. | Extender precisión, estructuras y conversión. Distinguir un Hilbert FIR de la señal analítica FFT y un modelo ADC/DAC de una cuantización ideal. |
| 08 | Editor de realización, espacio de estados MIMO, controlabilidad/observabilidad, lugar de raíces, tiempo de subida y establecimiento, sobreimpulso, ROC, fracciones parciales y vistas complejas. | Extender diagramas y análisis con puertos, relojes, simulación y métodos numéricos. El análisis SVD interno de rango y el CAS aportan primitivas, con requisitos diferentes de una herramienta general. |
| 09 | Resultados reutilizables, JSON/SLPROJ/SLBIN, Core Python y CLI, pipelines, campañas, procedencia, comparación y recuperación. | Unificar flujo entre disciplinas y conservar esquemas y rutas. |
| 10 | STFT inversa, FFT/PSD, I/Q, retardo fraccionario en canales, trenes y medidas de cruces, y convolución por bloques sobre un registro. | Extender las familias a flujos continuos, wavelets, adquisición e instrumentos. Separar evidencia de software del soporte de un dispositivo concreto. |
| 11 | Instrumentación y auditorías por candidato ya disponibles. | Ampliar su alcance a la calificación integral con mediciones auditables. |

Las filas del plan detallan prioridad, límite, activos de reutilización, dependencias, impacto en interfaz, compatibilidad y prueba pendiente por herramienta. [Matrices por fase](TOOL_MODERNIZATION_PLAN.md)

## Dependencias y riesgos

| Dominio | Riesgo que deberá delimitarse | Evidencia antes de calificar |
| --- | --- | --- |
| Estadística | Colas, covarianzas mal condicionadas, dependencia y reproducibilidad de RNG. | Oráculos en distribuciones y procesos, supuestos de incertidumbre, semillas/versiones y presupuestos de campañas. |
| RF y punto fijo | Convenciones por puerto, redes singulares, versión Touchstone, redondeos y acumuladores que alteran comportamiento. | Conversiones independientes, intercambio y vectores bit-exact con límites de palabra y fracción. |
| Simulación y datos | Ciclos algebraicos, incompatibilidad de unidades y relojes, pérdida de procedencia y migración de esquemas. | Reapertura histórica, soluciones analíticas, validación de puertos, costos de persistencia y recuperación transaccional. |
| SDR e instrumentación | Drivers y ABI por plataforma, discontinuidades de flujo, coste de soporte y paquetes mayores. | Arranque sin hardware, evidencia por dispositivo, registros de pérdida y equivalencia de bloques. |
| Distribución y calidad | La matriz actual tiene entradas específicas de Fases 03 y 04. El publicador valida el canal general y los comprobantes, mientras la familia exacta de cada fase se controla en la planificación. | Autorizar antes de implementar la ruta de Quality Gate de 2.3.x y cualquier guardia automatizada adicional. Preservar firma, hashes, canales y versiones históricas. |

La calificación de cada tecnología requiere licencias, mantenimiento, precisión, compatibilidad, seguridad y coste de distribución. Se mantienen los límites de los perfiles operativos acreditados, la restricción de MAT confiable y el seguimiento independiente de E-04. [Catálogo de integración](INTEGRATION_CATALOG.md) · [Adaptaciones de publicación](../development/releases.md#adaptaciones-pendientes-del-flujo)

## Coherencia documental

Se corrigió la secuencia futura, el estado de Fase 04 en los documentos vigentes, la descripción de `main` como estado aprobado, el permiso de Preview y la obligatoriedad de escalado. Los informes y decisiones históricos conservan la numeración y las condiciones con las que se emitieron. La Fase 05 requiere aprobación y planificación propias. Las brechas funcionales de infraestructura quedan registradas hasta obtener autorización para su cambio.

La verificación editorial recorrió 258 enlaces, imágenes y anclas locales de los 19 archivos de la entrega. También comprobó las tablas, la secuencia oficial de fases y familias, el inventario de archivos y el alcance del diff. La evidencia de las fases ejecutadas conserva su árbol histórico.

| Archivos del cambio | Finalidad |
| --- | --- |
| [README.md](../../README.md), [CONTRIBUTING.md](../../CONTRIBUTING.md), [docs/README.md](../README.md), [docs/roadmap.md](../roadmap.md) | Acceso a planificación, contribuciones, modernización y estado real. |
| [VISION.md](VISION.md), [ROADMAP.md](ROADMAP.md), [BACKLOG.md](BACKLOG.md), [PROJECT_STATE.md](PROJECT_STATE.md) | Dirección, fases, decisiones pendientes y referencias de integración. |
| [ARCHITECTURE_TO_BE.md](ARCHITECTURE_TO_BE.md), [ADR-004](ADR-004-INCREMENTAL-ENGINEERING.md), [INTEGRATION_CATALOG.md](INTEGRATION_CATALOG.md) | Monolito modular, reutilización, contratos, dependencias y límites. |
| [TOOL_MODERNIZATION_PLAN.md](TOOL_MODERNIZATION_PLAN.md), [UX_DESIGN_PRINCIPLES.md](UX_DESIGN_PRINCIPLES.md) | Inventario, matrices y políticas de interfaz. |
| [RELEASE_POLICY.md](RELEASE_POLICY.md), [VALIDATION_MATRIX.md](VALIDATION_MATRIX.md) | Gates permanentes, controles, distribución y alcance manual. |
| [docs/development/README.md](../development/README.md), [architecture.md](../development/architecture.md), [releases.md](../development/releases.md) | Orientación operativa, vínculos de arquitectura y brechas de infraestructura. |
| Este informe | Estado auditado, comparación, solapamientos y trazabilidad del cambio. |

## Alcance de la entrega

El commit se limita a documentación en `develop`. El punto de `main` sigue en la integración aprobada de Fase 04, `0c9e3bc`. No se inicia ninguna fase nueva, no se realiza merge ni se publica una versión. Las etiquetas, la línea Stable/LTS, los motores, las claves y la infraestructura de publicación quedan fuera de esta intervención.
