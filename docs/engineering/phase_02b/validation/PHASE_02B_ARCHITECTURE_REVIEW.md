# Revisión de arquitectura de Fase 02B

| Antes | Después |
| --- | --- |
| DFT definía su propio contexto. | DFT y los adaptadores DSP comparten `ExecutionContext` con presupuesto, progreso y observador local al hilo. |
| IDFT, filtrado, tasa y PSD se invocaban directamente desde paneles. | Los motores conservan su API. Los accesos pasan por solicitudes de aplicación específicas. |
| El proyecto sólo sabía de resultados sueltos. | El flujo prepara resultados en memoria y publica todas sus dependencias juntas en el proyecto. |
| La CLI sólo cubría DFT. | Los comandos reutilizan carga, ejecución y escritura de sesión y sirven operaciones individuales y un flujo. |
| Los archivos de señales eran de intercambio textual. | Una API opcional preserva una señal binaria en un archivo verificado por digest. |

Los servicios reutilizan los modelos y una secuencia DSP fija. Separan procedencia científica de telemetría. El costo residual se concentra en conservar los resultados en memoria y serializar proyectos JSON. La evidencia de rendimiento contiene el mapa de dependencias directas. Las pruebas headless acompañan el flujo de CI.
