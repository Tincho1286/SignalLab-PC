# Quality Gate de Fase 05

- **Candidato.** Familia 2.3.x, canal Preview y mismo SHA limpio en Windows Server 2022 y Ubuntu 22.04. El verificador debe conservar los controles de Engineering Core, comunicaciones y canal y rechazar cambios de SHA, evidencias ausentes y recibos incompatibles.
- **Cobertura.** Líneas globales ≥85 % y ramas globales ≥75 %. Componentes críticos ≥90 % de líneas y ≥85 % de ramas. Se conserva el conjunto previo y se incorporan los motores científicos de distribución, estadística/inferencia, ruido y procesos, identificación, PSD, estimación/filtrado, experimentos y servicios de aplicación, CLI y persistencia que se agreguen. Los nombres de estos módulos se fijan en el registro antes de medir. Denominadores y exclusiones conservan criterios auditables.
- **Defectos.** Todas las pruebas obligatorias aprobadas, cero P0 abiertos y cero P1 internos pendientes.
- **Ciencia y compatibilidad.** Oráculos independientes, campañas estadísticas, regresiones acumuladas, cinco demostradores, paridad Workbench/Python/CLI donde aplica e independencia del motor respecto de Qt. Pruebas funcionales automatizadas de interfaz en ambos sistemas. Las pruebas manuales de DPI son diagnósticas.
- **Recursos.** Medir RSS y tiempo de perfiles de generación, matrices, estimadores, espectros, Kalman, adaptación y campañas. Verificar cancelación, reintento concurrente, recuperación y persistencia atómica. En los perfiles aprobados, conservar los criterios previos de hasta 1,5 s desde la petición de cancelación y hasta 2 s entre eventos de interfaz. Los perfiles y tamaños son evidencia de admisión cooperativa.
- **Publicación.** Portables e instaladores, fuentes, inventarios, documentación, hashes, procedencia y manifiesto firmado. Mantener separación de 2.0.x y verificar descarga y firma desde la Release pública. La autorización de inicio permite publicar una Preview calificada. La aceptación funcional y la integración requieren decisiones propias.

## Registro de componentes críticos

| Paquete | Módulos comprometidos antes de implementar |
| --- | --- |
| WP-01 | `probability.py`, `multivariate_probability.py` y el adaptador headless `probability_cli.py`. |
| WP-02 | `descriptive_statistics.py`, `statistical_inference.py`, `statistics_results.py` para entrega y el adaptador headless `statistics_cli.py`. |
| WP-03 | `stochastic_processes.py` para transiciones y realizaciones, `stochastic_noise.py` para ruido, `stochastic_covariance.py` para correlación y covarianza, la CLI `stochastic_cli.py` y la entrega `realization_batch.py`. |
| WP-04 | `ar_estimation.py`, `time_series_identification.py` para ajuste, `random_models.py` para análisis teórico y el adaptador headless que exponga los ajustes y su procedencia. |
| WP-05 | `statistical_spectra.py` para los estimadores ampliados y las fronteras existentes `dsp_application.py` y `fourier.py` donde corresponda. |

[Protocolo estadístico](STATISTICAL_VALIDATION_PROTOCOL.md) · [Validación permanente](../VALIDATION_MATRIX.md#criterios-vigentes) · [Política de entregas](../RELEASE_POLICY.md)
