# Revisión estratégica posterior a Fase 05

Auditoría del 27 de noviembre de 2026. El punto de partida fue `10fe3f218de2cdf183a4cc282ebd54aed403a981`, verificado en `main` y `develop` locales y remotos. Los dos worktrees estaban limpios. GitHub registraba únicamente `main` y `develop` como ramas remotas. [Comprobante de auditoría](evidence/post-phase-05-baseline.json)

## Estado del proyecto y evidencia

| Control | Resultado observado |
| --- | --- |
| Cierre y aceptación | El propietario probó los gráficos de 2.3.1 Preview, aceptó el resultado y autorizó el cierre de Fase 05 y el merge. [Acta](phase_05/DECISION_LOG.md#aceptación-de-231-y-autorización-de-integración) |
| Candidato publicado | `v2.3.1` apunta a `1311df1f0f954f06eaf5f20c33f645d15748660a`. La Release pública conserva la marca Preview y los 17 adjuntos verificados. [Release](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.3.1) · [Recibo](phase_05/evidence/candidate-1311df1/publication.json) |
| Calificación acumulada | En Windows Server 2022 y Ubuntu 22.04 pasaron 1 437 pruebas integrales, 150 casos preventivos y 384 contrastes científicos por plataforma. Líneas y ramas fueron 90,06 % y 77,71 % en Windows, y 90,01 % y 77,70 % en Ubuntu. [Matriz](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46070995974) · [Quality Gate](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.3.1/quality-gate-05.json) |
| Integración | El árbol del merge `9474626` coincide con `develop` aceptado. Entre el candidato y la base auditada solo cambió documentación. Los cinco controles del merge aprobaron en GitHub. [Integración](phase_05/PHASE_05_INTEGRATION.md) · [Controles](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46076665338) |
| Stable/LTS y Preview | GitHub selecciona `v2.0.0` como última estable. Su etiqueta apunta a `adfad5c093a236b0565f00f5e97845acf040ec96`. El actualizador verificó los manifiestos y seleccionó 2.0.0 en Stable y 2.3.1 en Preview. [LTS](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.0.0) · [Política](RELEASE_POLICY.md) |

Los perfiles de 2.3.1 en CI midieron RSS máximo de 132,48 MiB en Windows y 152,30 MiB en Ubuntu. Los mayores intervalos del pulso Qt offscreen fueron 76,52 y 98,45 ms. Las máximas latencias observadas de cancelación cooperativa fueron 0,569 y 0,808 ms en sus puntos de prueba. Los resultados corresponden a los perfiles registrados. La medición de navegación de Fase 05 usa un recorrido distinto y conserva su contexto. [Comprobantes](evidence/post-phase-05-baseline.json) · [Protocolo de rendimiento](phase_05/PERFORMANCE_REPORT.md)

El SBOM e inventario corresponden a los binarios de 2.3.1. Se cotejaron CPython 3.14.10, Expat 2.9.0, Qt 6.12.1, la exclusión de JPEG 2000 en Pillow y la procedencia de OpenSSL en Linux. La matriz validó el salto aislado de 2.0.0 a 2.3.1 con sesión conservada y rechazo de una descarga alterada. En Fedora se comprobó el acceso del portable candidato al feed público que estaba vigente al ejecutarse la matriz. La publicación posterior acredita la selección de 2.3.1 en ese feed. [Dependencias y SBOM](DEPENDENCY_AUDIT.md#línea-base-de-la-entrega-231) · [Construcción](phase_05/evidence/candidate-1311df1/verified-build.json) · [Actualización pública](phase_05/evidence/candidate-1311df1/publication.json)

## Capacidades, límites y deuda

El inventario distingue **51 herramientas en 8 áreas**, **105 rutas canónicas**, **25 rutas de agrupación o compatibilidad** y los accesos transversales. Los métodos que comparten un problema se agrupan por tarea. La revisión cotejó el catálogo activo con los selectores de cada motor, incluidos rótulos que conservan nombres históricos. El informe de cobertura identifica **53 componentes críticos** del Gate acumulado. [Herramientas](TOOL_INVENTORY.md) · [Motores y críticos](SCIENTIFIC_ENGINE_INVENTORY.md)

El grafo confirma el monolito modular con servicios compartidos y puntos de acoplamiento diferido. Se bloquearon las importaciones Qt al cargar 23 módulos representativos. Una DFT sobre índices no nulos se comparó con suma directa y se invirtió preservando el origen. El ensayo acredita esas fronteras. Los recorridos heredados se consolidan mediante pruebas de paridad por operación. [Arquitectura observada](ARCHITECTURE_AS_IS.md#línea-base-posterior-a-fase-05) · [Arquitectura objetivo](ARCHITECTURE_TO_BE.md) · [Evidencia](evidence/post-phase-05-baseline.json)

El alcance operativo conserva MAT confiable, admisión de memoria estimada y cancelación cooperativa en los perfiles medidos. Los bloqueos de campañas se acreditan en almacenamiento local. E-04 sigue como seguimiento de Authenticode independiente del manifiesto firmado. La inferencia espectral de Bartlett y el Kalman lineal discreto conservan sus condiciones científicas. Entre las tareas de consolidación quedan la paridad de recorridos históricos, el transporte común de unidades y reloj y el ajuste de rótulos a las variantes reales. [Riesgos](RISK_REGISTER.md#situación-posterior-a-fase-05) · [Deuda](TECHNICAL_DEBT.md#prioridades-activas-posteriores-a-fase-05)

## Dictamen de preparación para Fase 06

**Base técnica apta para solicitar autorización de inicio.** Las fronteras DSP, LTI, propagación y estadística ya calificadas permiten preparar RF analítica en el monolito modular. La autorización habilitaría definir contratos, requisitos, oráculos y presupuesto del dominio. La capacidad RF multipuerto y su gate quedan por calificar en 2.4.x. [Plan de RF](TOOL_MODERNIZATION_PLAN.md#fase-06--rf-y-microondas)

| Prioridad propuesta para el inicio autorizado | Decisión y criterio de salida |
| --- | --- |
| 1 · Contrato de red | Fijar dominio de frecuencia, forma de matrices, orden de puertos, impedancia de referencia, definición de ondas y signo de corrientes. Probar redes pasivas, recíprocas y singulares en conversiones y cascadas. Usar `Transfer` para filtros escalares compatibles. |
| 2 · Referencias y archivos | Fijar el subconjunto Touchstone, versiones, unidades, límites y fallos de lectura. Contrastar carga adaptada, línea conocida, abierto/cortocircuito y dos puertos con ecuaciones, IBIS y comparadores aislados. Registrar licencia, versiones y tolerancias. |
| 3 · Modernización y enlace | Integrar Bessel y sensibilidad al diseñador, evaluación de retardo cuando la fase es válida, Zoom FFT/CZT y ventanas en las familias existentes. Reutilizar propagación y potencias para el presupuesto de enlace, distinguir figura de ruido, sensibilidad y modelos de compresión/intermodulación. |
| 4 · Interfaz y calificación | Ubicar las tareas RF con variantes, figuras y reuso de resultados. Medir cada tramo de rendimiento. Incorporar componentes críticos RF, preservar toda la regresión anterior y calificar la misma fuente en Windows y Linux sin hardware RF. |

SciPy ya está en el lock y aporta primitivas para DSP. scikit-rf se propone como comparador de redes y ngspice como proceso externo de referencia para circuitos de CA. La adopción de un adaptador requiere evidencia propia y decisión de alcance. [Evaluación y fuentes](INTEGRATION_CATALOG.md#referencias-y-modalidades-de-integración)

## Comprobaciones de esta actualización

Se cotejaron las ramas y etiquetas públicas, las dos ejecuciones de GitHub, la firma del feed y las huellas de los adjuntos. El inventario se contrastó con las 51 entradas del catálogo, los 53 nombres del informe crítico y los archivos de pruebas citados. El ensayo sin Qt comparó la DFT con suma directa, con error absoluto máximo de 9,93 × 10⁻¹⁶, y recuperó las muestras y el origen con la IDFT.

Pasaron la revisión de enlaces y anclas, las tablas, la secuencia de 14 fases y subfases, sus familias y el alcance documental del diff. La matriz acumulada citada corresponde al candidato publicado 2.3.1. Las comprobaciones de esta revisión se limitaron a la procedencia, la auditoría de código y la coherencia documental.

## Documentación entregada

| Área | Archivos |
| --- | --- |
| Dirección y planificación | [Visión](VISION.md), [roadmap y dependencias entre fases](ROADMAP.md), [estado del proyecto](PROJECT_STATE.md), [backlog](BACKLOG.md) y [modernización](TOOL_MODERNIZATION_PLAN.md). |
| Inventarios | [Herramientas y variantes](TOOL_INVENTORY.md) y [motores y críticos](SCIENTIFIC_ENGINE_INVENTORY.md). |
| Arquitectura, interfaz y metodología | [Arquitectura observada](ARCHITECTURE_AS_IS.md), [arquitectura objetivo](ARCHITECTURE_TO_BE.md), [ADR 004](ADR-004-INCREMENTAL-ENGINEERING.md), [Workbench](UX_DESIGN_PRINCIPLES.md) y [guía de arquitectura](../development/architecture.md). |
| Ciencia, calidad y riesgos | [Validación](VALIDATION_MATRIX.md), [auditoría matemática](MATHEMATICAL_AUDIT.md), [dependencias](DEPENDENCY_AUDIT.md), [integración científica](INTEGRATION_CATALOG.md), [riesgos](RISK_REGISTER.md) y [deuda](TECHNICAL_DEBT.md). |
| Desarrollo y entregas | [Política de entregas](RELEASE_POLICY.md), [desarrollo](../development/README.md), [guía de dependencias](../development/dependencies.md) y [distribución](../development/releases.md). |
| Evidencia de esta revisión | Este informe y [comprobante de la línea base](evidence/post-phase-05-baseline.json). El SHA documental se registra en Git, con la línea base auditada como su predecesora. |

Esta entrega se limita a planificación y documentación en `develop`. El cierre de Fase 05 y las publicaciones existentes conservan su evidencia. El inicio funcional de Fase 06 queda sujeto a autorización expresa.
