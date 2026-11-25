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
