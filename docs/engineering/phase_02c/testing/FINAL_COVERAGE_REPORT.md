# Cobertura de la Fase 02C

## Medición focal de la siguiente revisión

Se combinaron las líneas y arcos del último candidato integral `eb50895` con ocho grupos de pruebas focales ejecutados en Windows con CPython 3.14.10. En los archivos de cálculo modificados se trasladaron sólo las líneas históricas que se conservan y los arcos cuyos extremos permanecen en el código. Se mantuvo el alcance de instrumentación de la aplicación. Esta proyección sirve para priorizar pruebas adicionales. La cobertura definitiva requiere la suite integral sobre el candidato limpio.

| Base integral y pruebas focales agregadas | Líneas proyectadas | Ramas proyectadas | Líneas adicionales para 85 % | Ramas adicionales para 75 % |
| --- | ---: | ---: | ---: | ---: |
| Windows | 36 135/42 687 (84,65 %) | 11 596/16 420 (70,62 %) | 149 | 719 |
| Ubuntu | 36 116/42 687 (84,61 %) | 11 595/16 420 (70,62 %) | 168 | 720 |

La proyección de Ubuntu aplica los arcos locales a su línea base histórica. Las nuevas pruebas del candidato en ese sistema quedan pendientes. E-06a y E-06b siguen abiertos. Las brechas restantes se concentran en las rutas de despacho, cancelación, restauración, análisis simbólico y escritorio.

La ampliación posterior agregó ensayos de rejillas y líneas espectrales desde fórmulas, validación de conversiones, filtros clásicos, comparación de ventanas, importación MAT y restauración de formularios.

| Base integral y trece grupos focales | Líneas proyectadas | Ramas proyectadas | Ramas adicionales para 75 % |
| --- | ---: | ---: | ---: |
| Windows | 36 492/42 718 (85,43 %) | 11 820/16 436 (71,92 %) | 507 |
| Ubuntu | 36 473/42 718 (85,38 %) | 11 819/16 436 (71,91 %) | 508 |

El objetivo de líneas queda superado en la proyección. La validación de ambos objetivos exige un candidato integral. La instrumentación y sus exclusiones conservan la configuración del último candidato.

La continuación con análisis de expresiones, lecturas de retardo y borradores de sesión registra 36 534/42 754 líneas y 11 842/16 454 ramas proyectadas sobre Windows (85,45 % y 71,97 %). Sobre la base Ubuntu proyecta 36 515 líneas y 11 841 ramas (85,41 % y 71,96 %). Faltan respectivamente 499 y 500 ramas para 75 %. Los resultados se usan para priorizar la siguiente ampliación y no acreditan la matriz.

El lote de conversiones, RC y traspaso Z amplió la proyección a 36 572/42 772 líneas y 11 861/16 460 ramas en Windows (85,51 % y 72,06 %). Sobre la base Ubuntu proyecta 36 553 líneas y 11 860 ramas (85,46 % y 72,05 %). Faltan 484 ramas en Windows y 485 en Ubuntu. El resultado sigue siendo una combinación focal sobre la matriz histórica.

## Historial de mediciones integrales

Se midieron líneas y ramas con coverage.py en `459b9fc`. La suite subió de 850 a 870 pruebas, con 150 casos preventivos por plataforma. La cobertura global de líneas pasó de 77,96 % a 78,09 % en Windows y de 77,94 % a 78,06 % en Ubuntu. La de ramas subió de 63,61 % a 63,84 % y de 63,60 % a 63,82 %, respectivamente.

| Componente | Objetivo líneas / ramas | Resultado líneas / ramas | Excepción pendiente |
| --- | --- | --- | --- |
| Aplicación Windows | 85 % / 75 % | 78,09 % / 63,84 % | E-06a líneas, E-06b ramas |
| Aplicación Ubuntu | 85 % / 75 % | 78,06 % / 63,82 % | E-06a líneas, E-06b ramas |
| Muestreo | 90 % / 85 % | 92,11 % / 75,38 % | E-06c ramas |
| Fourier | 90 % / 85 % | 91,83 % / 61,90 % | E-06d ramas |
| Contexto de ejecución | 90 % / 85 % | 100 % / 100 % | Cumple |
| Frontera DFT | — / 85 % | 92,86 % / 66,67 % | E-06e ramas |
| Adaptadores DSP | 90 % / 85 % | 96,52 % / 80,00 % | E-06f ramas |
| Pipeline | 90 % / 85 % | 92,54 % / 77,27 % | E-06g ramas |
| Almacenamiento científico | 90 % / 85 % | 91,58 % / 80,00 % | E-06h ramas |
| Sesión CLI | 90 % / 85 % | 96,88 % / 100 % | Cumple |
| Huellas de procedencia | — / 85 % | 88,46 % / 75,00 % | E-06i ramas |
| Proyecto | — / 85 % | 95,87 % / 84,68 % | E-06j ramas |

Los módulos coincidieron en ambas plataformas. Se aplicó el objetivo de ramas a las rutas de procedencia en Proyecto y al módulo de huellas. Las siete pruebas específicas de procedencia cubren sustitución de señales, reloj, sistemas, parámetros, cambios durante y después de calcular, reapertura y filtros históricos. El banco y los contratos también verifican publicación atómica y compatibilidad.

La aplicación tiene 41 991 líneas instrumentadas y 16 174 ramas. Con esos denominadores actuales, alcanzar los objetivos en Ubuntu requeriría cubrir al menos otras 2 913 líneas y 1 809 ramas. La brecha se concentra en despacho de herramientas, paneles, escritorio y edición gráfica. Los casos agregados se concentraron en resultados observables del Core. El déficit de ramas de los motores sigue siendo una condición de revisión para variantes, validaciones y rutas de error fuera de los perfiles probados. [Datos por módulo](../validation/evidence/ci-459b9fc.json) · [Registro de aprobaciones](../validation/EXCEPTION_APPROVAL_REGISTER.md)

## Continuidad sobre faef335

Matriz 45673548563 del 25/11/2026. Suite de 890 pruebas, con 150 casos preventivos por plataforma, frente a 870 pruebas del expediente anterior. Se ejecutó la misma configuración de cobertura. Los denominadores cambiaron al instrumentar código nuevo del lector, el contenedor y las rutas de escritorio. Se conservan los objetivos y las exclusiones previas.

| ID | Componente | Líneas Windows / Linux | Ramas Windows / Linux | Verificación |
| --- | --- | ---: | ---: | --- |
| E-06a | Aplicación. Objetivo 85 % de líneas | 78,67 % / 78,61 % | — | Abierta |
| E-06b | Aplicación. Objetivo 75 % de ramas | — | 64,60 % / 64,59 % | Abierta |
| E-06c | Muestreo | 99,67 % / 99,67 % | 93,85 % / 93,85 % | Cumple |
| E-06d | Fourier | 99,61 % / 99,61 % | 85,71 % / 85,71 % | Cumple |
| E-06e | Frontera DFT | 100 % / 100 % | 100 % / 100 % | Cumple |
| E-06f | Adaptadores DSP | 98,51 % / 98,51 % | 90,00 % / 90,00 % | Cumple |
| E-06g | Pipeline | 96,27 % / 96,27 % | 95,45 % / 95,45 % | Cumple |
| E-06h | Almacenamiento científico SLBIN | 94,74 % / 94,74 % | 90,00 % / 90,00 % | Cumple |
| E-06i | Huellas de procedencia | 94,34 % / 94,34 % | 85,00 % / 85,00 % | Cumple |
| E-06j | Proyecto | 95,62 % / 95,62 % | 85,51 % / 85,51 % | Cumple |
| — | Contexto de ejecución | 100 % / 100 % | 100 % / 100 % | Cumple |
| — | Sesión CLI | 96,88 % / 96,88 % | 100 % / 100 % | Cumple |

En Windows se cubrieron 33 370 de 42 420 líneas y 10 550 de 16 332 ramas. En Ubuntu se cubrieron 33 346 líneas y 10 548 ramas de los mismos denominadores. Los objetivos exigen otras 2 687 líneas y 1 699 ramas en Windows y 2 711 líneas y 1 701 ramas en Linux. Los cinco archivos de escritorio que más concentran líneas sin cubrir en Linux son `toolbox.py` (459), `ui.py` (241), `workbench.py` (216), `course_tools_panel.py` (202) y `pole_zero_editor.py` (200). Un subconjunto de deuda adicional está en los comandos de instalación Linux y la tabla de resultados. La medición se conserva para orientar nuevos flujos de validación, error, cancelación y recuperación.

`project_archive.py` es código nuevo incluido en el denominador global. Por separado mide 86,11 % de líneas y 64,00 % de ramas en ambos sistemas. Quedan rutas de error del manifiesto y de admisión por cubrir antes de ampliar el uso a proyectos grandes. Las verificaciones actuales incluyen persistencia y reapertura, procedencia, JSON histórico, truncamiento, digest incorrecto y cancelación antes del reemplazo.

[Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45673548563) · [Resultados estructurados](../validation/evidence/ci-faef335.json)

## Continuación autónoma sobre 54adaa0

La corrida 45683218209 aplicó la misma instrumentación y alcanzó 907 pruebas integrales y 150 casos preventivos por sistema. SLPROJ alcanzó 101/106 líneas y 41/46 ramas en ambos sistemas. La hoja CAS headless cubrió su contrato. El controlador de sesiones siguió como componente crítico bajo objetivo en ese candidato.

| Alcance | Windows | Linux | Objetivo |
| --- | ---: | ---: | ---: |
| Líneas de aplicación | 34 006/42 600 (79,83 %) | 33 981/42 600 (79,77 %) | 85 % |
| Ramas de aplicación | 10 771/16 398 (65,68 %) | 10 768/16 398 (65,67 %) | 75 % |
| Líneas adicionales necesarias | 2 204 | 2 229 | — |
| Ramas adicionales necesarias | 1 528 | 1 531 | — |
| SLPROJ | 95,28 % / 89,13 % | 95,28 % / 89,13 % | 90 % / 85 % |

La matriz de `54adaa0` es evidencia histórica para la continuación. Las pruebas posteriores cubren reapertura de CAS con foco, cambios de generación, permisos, normalización, interconexión, cuantización, fase y navegación en tablas. El ensayo local de 39 pruebas sobre `3a68618` midió 318/348 líneas y 128/154 ramas del controlador de sesiones. Se agregaron después regresiones sobre descarte explícito y limpieza con archivos bloqueados. La mejora global sigue siendo deuda de verificación y se mide en el [candidato vigente](../validation/FINAL_VALIDATION_MATRIX.md#continuación-autónoma).

[Informe automático con métricas por archivo y prioridad](../validation/evidence/ci-54adaa0.json) · [Comando y pruebas](../IMPLEMENTATION_LOG.md)

## Medición integral de 3a68618

Las suites de ambos sistemas finalizaron con 917 pruebas integrales y 150 casos preventivos. El trabajo de empaquetado Windows tuvo un timeout separado. La cobertura de líneas subió a 81,09 % (34 587/42 651) en Windows y 81,03 % (34 562/42 651) en Linux. La de ramas llegó a 66,61 % (10 934/16 416) y 66,59 % (10 931/16 416). Para alcanzar los objetivos faltaron 1 667 líneas y 1 378 ramas en Windows y 1 692 líneas y 1 381 ramas en Linux.

El controlador de sesión alcanzó 318/348 líneas y 128/154 ramas en ambos sistemas. Las pruebas de recuperación posteriores alcanzaron localmente 328/348 líneas y 133/154 ramas en Windows. Ésta es una medición focal. Debe confirmarse en la matriz de aplicación. [Corrida 45685956523](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45685956523) · [Matriz vigente](../validation/FINAL_VALIDATION_MATRIX.md#continuación-autónoma)

## Medición integral de 99f7ce2

Las dos suites de 922 pruebas y 150 casos preventivos alcanzaron los mínimos de todos los componentes críticos controlados. El total global quedó en 81,35 % de líneas y 66,74 % de ramas en Windows y en 81,29 % / 66,72 % en Linux. El déficit fue de 1 557 líneas y 1 357 ramas en Windows y 1 582 líneas y 1 360 ramas en Linux. Los procesos de CI de distribución agotaron el plazo previo y sus artefactos de portables auditados, SBOM e instalación están incompletos para este SHA. [Resultado por condición](../validation/evidence/quality-gate-99f7ce2.json)

## Matriz completa de eb50895

| Medición | Windows | Linux | Objetivo |
| --- | ---: | ---: | ---: |
| Pruebas integrales | 925 | 925 | — |
| Casos preventivos | 150 | 150 | — |
| Líneas globales | 34 914/42 674 (81,82 %) | 34 889/42 674 (81,76 %) | 85 % |
| Ramas globales | 11 010/16 416 (67,07 %) | 11 007/16 416 (67,05 %) | 75 % |
| Líneas y ramas adicionales | 1 359 y 1 302 | 1 384 y 1 305 | — |
| SLPROJ, líneas / ramas | 95,33 % / 89,13 % | 95,33 % / 89,13 % | 90 % / 85 % |
| Controlador de sesión, líneas / ramas | 94,25 % / 86,36 % | 94,25 % / 86,36 % | 90 % / 85 % |
| Hoja CAS headless, líneas / ramas | 100 % / 100 % | 100 % / 100 % | 90 % / 85 % |

Cada componente crítico alcanzó sus objetivos en los dos sistemas. Linux concentra líneas pendientes en `toolbox.py` (415), `ui.py` (238), `workbench.py` (196), `linux_installation.py` (195) y `course_tools.py` (170). El índice incluye las 15 prioridades de líneas y ramas por sistema. [Datos reproducibles](../validation/evidence/ci-eb50895.json)
