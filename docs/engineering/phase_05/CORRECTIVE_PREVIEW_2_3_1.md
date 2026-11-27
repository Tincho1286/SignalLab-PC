# Correcciones de 2.3.1 Preview

La Preview de mantenimiento corresponde al candidato `1311df1f0f954f06eaf5f20c33f645d15748660a`. El selector actualiza el lanzador cuando aparece una figura que se había preparado con la pestaña oculta. Las tasas acumuladas comparten el cálculo de errores del informe y respetan los bits útiles. Los vectores I/Q representan los pares del tramo alineado. [Implementación y causa](IMPLEMENTATION_LOG.md#correcciones-para-231-preview) · [Novedades y descargas](../../releases/v2.3.1.md)

| Plataforma | Integrales | Preventivas | Contrastes científicos | Líneas | Ramas |
| --- | ---: | ---: | ---: | ---: | ---: |
| Windows Server 2022 | 1437 | 150 | 384 | 90,06 % | 77,71 % |
| Ubuntu 22.04 | 1437 | 150 | 384 | 90,01 % | 77,70 % |

El Quality Gate acumulado quedó aprobado sobre un solo SHA. Las regresiones abren la convergencia de Monte Carlo, el histograma bootstrap y las figuras de Wiener con registros, Kalman y filtrado adaptativo. La medición de calidad verifica tasas sin errores, conteo en más de un bloque, exclusión de relleno y coordenadas I/Q con desfases distintos. [Matriz](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46070995974) · [Quality Gate](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.3.1/quality-gate-05.json)

La verificación pública cotejó las huellas de todos los adjuntos. El actualizador autenticó el manifiesto y seleccionó 2.3.1 en Preview y 2.0.0 en Stable. `main` permanece en `0c9e3bcdafd89dfd4437b28a93f0606fa5116542`. La aceptación funcional, la integración y la Fase 06 quedan bajo decisión del propietario. [Procedencia](evidence/candidate-1311df1/verified-build.json) · [Publicación verificada](evidence/candidate-1311df1/publication.json)
