# Expediente de cierre de Fase 04

La calificación automatizada de 2.2.0 Preview aprobó sobre `a3026d288fe2371aace308b403071cf457b89123` en `develop`. La validación de escritorio real sigue abierta y el cierre técnico conserva el dictamen **NO-GO**. [Quality Gate](QUALITY_GATE_REPORT.md) · [Matriz del candidato](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45905864702)

## Resultados acreditados

- Los modelos multitrayecto, Rayleigh, Rician, Clarke, pérdidas, interferencia e imperfecciones comparten sus contratos y servicios entre Workbench, Python y CLI. El enlace conserva las convenciones de Fase 03 y declara cuándo los datos de sincronización impiden calcular métricas válidas. [Auditoría matemática](MATHEMATICAL_AUDIT.md) · [Trazabilidad](TRACEABILITY_MATRIX.md)
- Ambas plataformas aprobaron 1 254 pruebas y 150 casos preventivos. Los umbrales de cobertura global y crítica se cumplieron por conteos exactos. Se verificaron recuperación de campañas, cancelación y respuesta del escritorio offscreen para los perfiles medidos. [Recibos de pruebas y recursos](QUALITY_GATE_REPORT.md)
- Los portables e instaladores Windows y Linux se verificaron por SHA-256 junto con el código fuente, los inventarios y el salto aislado desde 2.0.0. Los artefactos de prueba preservan la separación entre Preview y Stable/LTS. [Paquetes candidatos](QUALITY_GATE_REPORT.md#paquetes-de-revisión-de-a3026d2) · [Notas](PREVIEW_NOTES.md)

## Evidencia y decisiones pendientes

El registro nativo de Windows cubre 1366 × 768 al 100 % con enlace, exportación, regreso al catálogo y distribuciones Rician. Clarke calculó y abrió ambas figuras al 125 % nativo. Con escalado de Qt, las ventanas entraron al 150 % y excedieron el alto útil al 200 %. El propietario confirmó el funcionamiento en Linux y autorizó la publicación de esta Preview con el recorte documentado y su corrección prevista para la próxima Preview. [Resultados y protocolo](VALIDATION_MATRIX.md) · [Notas de 2.2.0](../../releases/v2.2.0.md)

| Decisión | Dictamen | Condición pendiente |
| --- | --- | --- |
| Cierre técnico de Fase 04 | **NO-GO** | Verificar Windows nativo al 150 % y 200 % y el paquete 2.2.1 en Fedora Plasma. |
| Preparación para Fase 05 | **NO-GO** | Cerrar Fase 04 y emitir la recomendación basada en la evidencia completa. El inicio tiene autorización propia. |
| Distribución pública | **GO para 2.2.1 Preview** | Publicación autorizada sobre el SHA verificado. La revisión de escritorio del propietario queda pendiente. E-04 sigue como asunto independiente. |

La 2.2.0 Preview se publicó con 17 adjuntos verificados. La comprobación del actualizador en esa publicación validó su manifiesto firmado. [Publicación](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.2.0) · [Comprobante de publicación](evidence/candidate-a3026d2/publication-2.2.0.json)

La 2.2.1 Preview se publicó con el manifiesto firmado y 18 adjuntos verificados. El código `08cd1bc` incorpora el ajuste de altura y valida los certificados de GitHub con el almacén de Fedora. El actualizador ofrece 2.2.1 al incluir preliminares. Stable/LTS selecciona `v2.0.0`, y `main` conserva la integración aprobada de 2.1.1 Preview en `a94cd37`. [Publicación 2.2.1](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.2.1) · [Comprobante de publicación](evidence/candidate-08cd1bc/publication-2.2.1.json) · [Política de entregas](../RELEASE_POLICY.md)
