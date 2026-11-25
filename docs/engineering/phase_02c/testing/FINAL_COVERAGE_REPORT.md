# Cobertura de la Fase 02C

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
