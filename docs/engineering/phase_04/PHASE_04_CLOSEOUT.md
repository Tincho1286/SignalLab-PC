# Expediente de cierre de Fase 04

El propietario aprobó el cierre de Fase 04 y la integración en `main` el 27 de noviembre de 2026. El cierre toma como referencia `08cd1bc28189ef0c1cd6c5a36f2d9bd32f6f1a48`, el candidato publicado como 2.2.1 Preview. [Quality Gate](QUALITY_GATE_REPORT.md) · [Matriz del candidato](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45923696053/attempts/2)

## Resultados acreditados

- Los modelos multitrayecto, Rayleigh, Rician, Clarke, pérdidas, interferencia e imperfecciones comparten sus contratos y servicios entre Workbench, Python y CLI. El enlace conserva las convenciones de Fase 03 y declara cuándo los datos de sincronización impiden calcular métricas válidas. [Auditoría matemática](MATHEMATICAL_AUDIT.md) · [Trazabilidad](TRACEABILITY_MATRIX.md)
- La matriz de 2.2.0 registró 1 254 pruebas y 150 casos preventivos por plataforma, con los umbrales de cobertura cumplidos. La matriz de 2.2.1 volvió a aprobar la validación y la distribución en Windows Server 2022 y Ubuntu 22.04. [Recibos de pruebas y recursos](QUALITY_GATE_REPORT.md) · [Matriz de 2.2.1](evidence/candidate-08cd1bc/matrix-receipt.json)
- Los portables e instaladores Windows y Linux se verificaron por SHA-256 junto con el código fuente, los inventarios y el salto aislado desde 2.0.0. Los artefactos de prueba preservan la separación entre Preview y Stable/LTS. [Paquetes candidatos](QUALITY_GATE_REPORT.md#paquetes-de-revisión-de-a3026d2) · [Notas](PREVIEW_NOTES.md)

## Validación de escritorio

Antes de la corrección, Windows nativo se comprobó a 100 % y 125 %. El recorte a 200 % se reprodujo con escalado de Qt. En 2.2.1, la ventana principal y ambas figuras de Clarke cupieron en el área útil de 1366 × 768 con esa misma escala de Qt. En Fedora 44, el portable conectó con GitHub y verificó manifiestos de ambos canales. [Matriz de escritorio](VALIDATION_MATRIX.md) · [Windows al 200 % en Qt](evidence/candidate-08cd1bc/windows-clarke-qt-200.json) · [Fedora 44](evidence/candidate-08cd1bc/fedora-updates.json)

La comprobación nativa de Windows a 150 % y 200 % y la prueba interactiva en Fedora Plasma siguen como riesgos residuales. La aprobación de cierre queda registrada por separado de los resultados de cada prueba. [Decisión del propietario](DECISION_LOG.md#cierre-e-integración-de-fase-04) · [Riesgos residuales](RESIDUAL_RISK_REGISTER.md)

## Dictámenes

| Decisión | Dictamen | Alcance |
| --- | --- | --- |
| Cierre de Fase 04 | **Aprobado** | La matriz de 2.2.1 aprobó y el propietario autorizó el cierre y la integración. Los pendientes de escritorio conservan su seguimiento. |
| Preparación para Fase 05 | **Pendiente de evaluación** | La fase requiere un dictamen de continuidad y autorización independiente. |
| Distribución pública | **GO para 2.2.1 Preview** | Publicación completada sobre el SHA verificado. E-04 sigue como asunto independiente. |

La 2.2.0 Preview se publicó con 17 adjuntos verificados. La comprobación del actualizador en esa publicación validó su manifiesto firmado. [Publicación](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.2.0) · [Comprobante de publicación](evidence/candidate-a3026d2/publication-2.2.0.json)

La 2.2.1 Preview se publicó con el manifiesto firmado y 18 adjuntos verificados. El actualizador ofrece 2.2.1 al incluir preliminares y selecciona `v2.0.0` en Stable/LTS. [Publicación 2.2.1](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.2.1) · [Comprobante de publicación](evidence/candidate-08cd1bc/publication-2.2.1.json) · [Política de entregas](../RELEASE_POLICY.md)
