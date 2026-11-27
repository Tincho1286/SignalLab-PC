# Validación de Fase 05

Windows Server 2022 y Ubuntu 22.04 aprobaron la matriz completa sobre el mismo candidato `bde8eaa10bdfb878c22f6dad0c5a93a5e6c932fe`. Los controles de desarrollo sobre `d4a38ff` quedan como registro del preflight. [Matriz aprobada](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46059832440) · [Resultados cuantitativos](QUALITY_GATE_REPORT.md)

| Control | Evidencia de desarrollo | Evidencia emitida por la matriz |
| --- | --- | --- |
| Requisitos estadísticos | 195 pruebas focalizadas. Oráculos deterministas, semillas fijas, comparación entre herramientas y preservación de la configuración. | `integral-checks.json`, `integral-checks-preventive.json`, `statistical-qualification.json` e informes A–E. |
| Cobertura | Métricas focalizadas y prueba de exclusión de procesos en Windows. Los casos añadidos ejercitan dimensiones, transformaciones y recuentos multivariados. | `coverage.json` y `baseline.json` de ambos sistemas. El informe de bloqueo combina los recorridos nativos e informa los denominadores completos. |
| Recursos y recuperación | Ocho perfiles en dos escalas. Cancelación cooperativa de cálculo, campaña y escritura. Recuperación, contención y ciclo de eventos en Windows. | `statistical-performance.json` y controles acumulados. |
| Navegación y persistencia | Regreso a borradores, destino de la señal, opciones de dos entradas, figuras y recuperación. Verificaciones específicas con Qt offscreen. | Suite integral de ambas plataformas y reportes de paquetes. |
| Plataformas y distribución | Controles de desarrollo de Windows y Ubuntu aprobados. | Instaladores y portables, inventarios, recibos, actualización aislada desde 2.0.0, comprobación del actualizador empaquetado en Fedora y procedencia común. |

Los comprobantes registran el origen de los paquetes y la disponibilidad de los adjuntos. Se verificaron el manifiesto firmado y la selección de versiones en los canales Preview y Stable. [Procedencia](evidence/candidate-bde8eaa/verified-build.json) · [Publicación](evidence/candidate-bde8eaa/publication.json)

[Controles de desarrollo](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46054912708) · [Criterios del Quality Gate](QUALITY_GATE_CRITERIA.md) · [Trazabilidad](TRACEABILITY_MATRIX.md)
