# Plan autorizado de Fase 05

El orden de desarrollo sigue las dependencias científicas. Cada paquete amplía herramientas compatibles y añade pruebas e interfaces en el mismo recorrido. Los criterios y el alcance permanecen sujetos a la directiva de Fase 05. [Requisitos](PHASE_05_REQUIREMENTS.md) · [Contratos](SCIENTIFIC_CONTRACTS.md)

| Paquete | Trabajo y dependencia principal | Evidencia de salida |
| --- | --- | --- |
| WP-00 | Línea base, auditoría, contratos, protocolos y adaptación incremental del Quality Gate. | Recibos del código anterior, requisitos trazables y verificador que rechaza evidencia incompleta. |
| WP-01 | Distribuciones univariadas, multivariadas y complejas. Modernizar Generar realización. | Densidad/masa, probabilidades, colas, cuantiles, momentos y muestras reproducibles reutilizables. |
| WP-02 | Estadística descriptiva e inferencia sobre entradas de WP-01 y otros laboratorios. | Informes descriptivos y ajuste, gráficos y pruebas con hipótesis e incertidumbre. |
| WP-03 | Ruido y procesos, covarianza y correlación. | Transiciones y estimadores con oráculos, comparación teoría/experimento y unidades de reloj. |
| WP-04 | Identificación y pronóstico, desde los modelos existentes. | Estacionariedad, identificabilidad, comparación de estimadores y error/predicción. |
| WP-05 | Estimación espectral ampliada. | Normalizaciones acreditadas, potencia, espectro cruzado, coherencia y observación irregular. |
| WP-06 | Estimación óptima y filtrado Wiener, Kalman, LMS/NLMS/RLS. | Errores, innovación, trayectorias, covarianzas y convergencia contrastados. |
| WP-07 | Monte Carlo, incertidumbre y campañas. | Semillas/subflujos, reanudación, exportación y cotas para probabilidades estimadas. |
| WP-08 | Workbench, API, CLI e integración entre laboratorios. | Demostradores A–E. Ayuda y paridad verificadas con las rutas productivas. |
| WP-09 | Calificación científica, compatibilidad, cobertura, rendimiento y seguridad. | Pruebas independientes y campañas, recursos, regresiones y riesgos registrados. |
| WP-10 | Matriz conjunta, empaquetado, firma y publicación 2.3.x. | Calidad, recibos y hashes vinculados al SHA, Release real y protocolo funcional. |

Usar SciPy, NumPy, SymPy y mpmath según el problema y mantener los oráculos separados del algoritmo comprobado. Statsmodels, FilterPy y SALib se consideran comparadores de auditoría antes de decidir si aportan algo al runtime. Una incorporación exige comprobar mantenimiento, licencia, CPython, Windows/Linux, seguridad, precisión y tamaño del paquete. [Arquitectura objetivo](../ARCHITECTURE_TO_BE.md) · [Catálogo de integración](../INTEGRATION_CATALOG.md)
