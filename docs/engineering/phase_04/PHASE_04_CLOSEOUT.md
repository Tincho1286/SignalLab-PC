# Expediente de cierre de Fase 04

La calificación automatizada de 2.2.0 Preview aprobó sobre `a3026d288fe2371aace308b403071cf457b89123` en `develop`. La validación de escritorio real sigue abierta y el cierre técnico conserva el dictamen **NO-GO**. [Quality Gate](QUALITY_GATE_REPORT.md) · [Matriz del candidato](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45905864702)

## Resultados acreditados

- Los modelos multitrayecto, Rayleigh, Rician, Clarke, pérdidas, interferencia e imperfecciones comparten sus contratos y servicios entre Workbench, Python y CLI. El enlace conserva las convenciones de Fase 03 y declara cuándo los datos de sincronización impiden calcular métricas válidas. [Auditoría matemática](MATHEMATICAL_AUDIT.md) · [Trazabilidad](TRACEABILITY_MATRIX.md)
- Ambas plataformas aprobaron 1 254 pruebas y 150 casos preventivos. Los umbrales de cobertura global y crítica se cumplieron por conteos exactos. Se verificaron recuperación de campañas, cancelación y respuesta del escritorio offscreen para los perfiles medidos. [Recibos de pruebas y recursos](QUALITY_GATE_REPORT.md)
- Los portables e instaladores Windows y Linux se verificaron por SHA-256 junto con el código fuente, los inventarios y el salto aislado desde 2.0.0. Los artefactos de prueba preservan la separación entre Preview y Stable/LTS. [Paquetes candidatos](QUALITY_GATE_REPORT.md#paquetes-de-revisión-de-a3026d2) · [Notas](PREVIEW_NOTES.md)

## Evidencia y decisiones pendientes

El registro nativo de Windows cubre 1366 × 768 al 100 % con enlace, exportación, regreso al catálogo y distribuciones Rician. Clarke calculó y abrió ambas figuras al 125 % nativo. Con escalado de Qt, las ventanas entraron al 150 % y excedieron el alto útil al 200 %. Quedan la comprobación nativa de Windows al 150 % y 200 %, la evaluación del recorte observado y la sesión en Linux real. [Resultados y protocolo](VALIDATION_MATRIX.md)

| Decisión | Dictamen | Condición pendiente |
| --- | --- | --- |
| Cierre técnico de Fase 04 | **NO-GO** | Completar y archivar el escritorio real en ambos sistemas. |
| Preparación para Fase 05 | **NO-GO** | Cerrar Fase 04 y emitir la recomendación basada en la evidencia completa. El inicio tiene autorización propia. |
| Distribución pública | **NO-GO** | Completar el Quality Gate y obtener autorización expresa para publicar, etiquetar y firmar. E-04 sigue como asunto independiente. |

La integración de 2.1.1 Preview mantiene `main` en `a94cd37`. Stable/LTS usa `v2.0.0`. La aceptación funcional de la futura publicación y la autorización de su integración se registrarán en los pasos previstos por la política. [Estado del proyecto](../PROJECT_STATE.md) · [Política de entregas](../RELEASE_POLICY.md)
