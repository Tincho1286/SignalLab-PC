# Informe del Quality Gate de Fase 04

**Estado en revisión.** La 2.2.0 Preview candidata corresponde a `2a0a3fd97e63bd766d09739d51dc9aab4e9e6efb`. La matriz se ejecuta sobre ese commit en Windows Server 2022 y Ubuntu 22.04. Los commits posteriores del expediente incorporan documentación y resultados. [Matriz de Actions](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45899563971)

## Evidencia disponible

| Control | Resultado | Evidencia |
| --- | --- | --- |
| Ciencia e interoperabilidad | Los contrastes independientes de Clarke, fase Rician y canales deterministas cumplieron sus tolerancias. El caso común de Workbench, Python y CLI conserva muestras, reloj, huellas y métricas. | [Auditoría](MATHEMATICAL_AUDIT.md) · [Paridad](evidence/candidate-2a0a3fd/windows-interface-parity.json) |
| Suite integral y cobertura | En ejecución en ambos sistemas. Los umbrales se evalúan por los conteos completos de cada trabajo. | [Criterios](QUALITY_GATE_CRITERIA.md) · [Matriz de Actions](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45899563971) |
| Recursos | Ambos runners midieron los tres perfiles exigidos, verificaron los archivos reabiertos y cumplieron límites de cancelación y respuesta offscreen. | [Tiempo, memoria y cancelación](PERFORMANCE_REPORT.md) |
| Paquetes | Instalador, portable, comprobantes y fuente verificados contra SHA-256. El enlace empaquetado y la actualización aislada desde 2.0.0 pasaron en ambos sistemas. | [Recibo](evidence/candidate-2a0a3fd/verified-package-receipt.json) · [Hashes](evidence/candidate-2a0a3fd/SHA256SUMS-2.2.0-CANDIDATE.txt) · [Seguridad](SECURITY_REVIEW.md) |
| Escritorio real | Windows a 100 % verificó enlace, guardado, regreso al catálogo y figura de distribuciones. Restan las comprobaciones nativas indicadas en el protocolo. | [Protocolo y registro](VALIDATION_MATRIX.md) |

## Paquetes de revisión

| Sistema | Contenido | Paquete de Actions |
| --- | --- | --- |
| Windows x64 | Portable `.exe`, instalador `.exe`, fuente `.zip` y comprobantes. | [Descargar Windows](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45899563971/artifacts/15156258546) |
| Linux x86_64 | Portable `.tar.gz`, instalador `.run` y comprobantes. | [Descargar Linux](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45899563971/artifacts/15155098928) |

La revisión compara el hash de cada ZIP de Actions con su recibo de origen y vuelve a calcular el hash de cada archivo interno. El ZIP de fuentes identifica el mismo commit candidato. El portable Windows incluye la licencia y los avisos embebidos. El portable Linux conserva la licencia, los avisos y el manifiesto del entorno. Los artefactos de Actions tienen retención hasta el 3 de diciembre de 2026. [Notas de 2.2.0 Preview](PREVIEW_NOTES.md) · [Recibo de paquetes](evidence/candidate-2a0a3fd/verified-package-receipt.json)

## Dictámenes vigentes

| Decisión | Dictamen | Condición para reconsiderarlo |
| --- | --- | --- |
| Cierre técnico de Fase 04 | **NO-GO** | Recibir el resultado integral, revisar cobertura y completar el escritorio real. |
| Preparación técnica para Fase 05 | **NO-GO** | Completar la revisión de Fase 04 y emitir el dictamen de continuidad sobre los resultados consolidados. Su inicio requiere autorización específica. |
| Distribución pública de la Preview | **NO-GO** | Completar el Quality Gate. La publicación, la etiqueta y las claves de producción requieren autorización separada. Stable/LTS conserva su canal 2.0.x. |

Los ensayos de actualización usan manifiestos de prueba y el seguimiento E-04 conserva su tratamiento independiente. La aprobación funcional del propietario se registra por separado de la matriz. [Riesgos residuales](RESIDUAL_RISK_REGISTER.md) · [Política de entregas](../RELEASE_POLICY.md).
