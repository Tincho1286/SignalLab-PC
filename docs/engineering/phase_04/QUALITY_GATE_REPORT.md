# Informe del Quality Gate de Fase 04

**Matriz automatizada aprobada.** El candidato de 2.2.0 Preview `a3026d288fe2371aace308b403071cf457b89123` se calificó sobre el mismo commit limpio en Windows Server 2022 y Ubuntu 22.04. Cada sistema aprobó 1 254 pruebas integrales y 150 casos preventivos, sin fallos, errores ni omisiones. Los instaladores, portables y fuentes corresponden al mismo SHA. El cierre conserva pendiente la validación de escritorio real. [Matriz](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45905864702) · [Recibo](evidence/candidate-a3026d2/matrix-receipt.json) · [Resultado automatizado](evidence/candidate-a3026d2/automated-gate-45905864702.json)

| Sistema | Líneas globales | Ramas globales | Mínimo de líneas críticas | Mínimo de ramas críticas |
| --- | ---: | ---: | ---: | ---: |
| Umbral | 85 % | 75 % | 90 % | 85 % |
| Windows Server 2022 | 89,22 % · 43 178/48 393 | 76,29 % · 13 741/18 012 | 94,08 % | 85,00 % |
| Ubuntu 22.04 | 89,16 % · 43 149/48 393 | 76,25 % · 13 735/18 012 | 94,08 % | 85,00 % |

El menor porcentaje de líneas críticas corresponde a `communications_pipeline.py` y el menor de ramas a `operation_provenance.py`. Se combinaron 173 archivos de cobertura de procesos simbólicos en cada plataforma. La revisión local reprodujo el dictamen de Actions a partir de los informes de cada sistema y verificó los hashes de los archivos recibidos. [Windows](evidence/candidate-a3026d2/windows-integral-receipt.json) · [Ubuntu](evidence/candidate-a3026d2/linux-integral-receipt.json) · [Criterios](QUALITY_GATE_CRITERIA.md)

## Evidencia de la matriz anterior

La matriz de `2a0a3fd97e63bd766d09739d51dc9aab4e9e6efb` terminó con Ubuntu cancelado. Se conservan los resultados de Windows y los recibos de distribución de ambas plataformas para esa revisión. [Matriz anterior](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45899563971) · [Recibo](evidence/candidate-2a0a3fd/matrix-receipt.json)

| Control | Resultado | Evidencia |
| --- | --- | --- |
| Ciencia e interoperabilidad | Los contrastes independientes de Clarke, fase Rician y canales deterministas cumplieron sus tolerancias. El caso común de Workbench, Python y CLI conserva muestras, reloj, huellas y métricas. | [Auditoría](MATHEMATICAL_AUDIT.md) · [Paridad](evidence/candidate-2a0a3fd/windows-interface-parity.json) |
| Suite integral y cobertura | Windows aprobó 1 254 pruebas, los 150 casos preventivos y los umbrales globales y de componentes críticos. Ubuntu registró un fallo en el barrido del Workbench y agotó el plazo del runner durante el cierre. | [Resultado de Windows](evidence/candidate-2a0a3fd/windows-integral-receipt.json) · [Registro de Ubuntu](evidence/candidate-2a0a3fd/ubuntu-integral-tail.txt) · [Control automatizado](evidence/candidate-2a0a3fd/automated-gate-45899563971.json) |
| Recursos | Ambos runners midieron los tres perfiles exigidos, verificaron los archivos reabiertos y cumplieron límites de cancelación y respuesta offscreen. | [Tiempo, memoria y cancelación](PERFORMANCE_REPORT.md) |
| Paquetes | Instalador, portable, comprobantes y fuente verificados contra SHA-256. El enlace empaquetado y la actualización aislada desde 2.0.0 pasaron en ambos sistemas. | [Recibo](evidence/candidate-2a0a3fd/verified-package-receipt.json) · [Hashes](evidence/candidate-2a0a3fd/SHA256SUMS-2.2.0-CANDIDATE.txt) · [Seguridad](SECURITY_REVIEW.md) |
| Escritorio real | Windows a 100 % verificó enlace, guardado, regreso al catálogo y figura de distribuciones. Restan las comprobaciones nativas indicadas en el protocolo. | [Protocolo y registro](VALIDATION_MATRIX.md) |

El informe de Windows se generó sobre un checkout limpio de `2a0a3fd`. Al combinar la instrumentación se identificaron 173 archivos de cobertura generados por procesos simbólicos. La prueba de reutilización de una respuesta en el CAS, que había excedido la espera anterior en la exploración local, aprobó en la matriz. [Línea base](evidence/candidate-2a0a3fd/windows-baseline.json) · [Recibo integral](evidence/candidate-2a0a3fd/windows-integral-receipt.json)

La espera de la prueba retenía el intérprete mientras el barrido avanzaba en un hilo de Qt. Al vencer su plazo, el cierre de la ventana con un cálculo activo podía mostrar un diálogo modal sin respuesta en el runner. La espera ahora alterna el procesamiento de eventos con una pausa que deja avanzar al trabajador Python. La limpieza cancela y espera los trabajos activos antes de cerrar. Los límites de espera de la prueba, las aserciones de resultados y los umbrales de cobertura se conservan. Las 14 pruebas focalizadas de Ubuntu aprobaron en 15,920 s con la instrumentación de la matriz y el barrido pasó también en la suite integral. [Investigación](IMPLEMENTATION_LOG.md#diagnóstico-del-barrido-en-ubuntu) · [Recibo focalizado](evidence/candidate-a3026d2/ubuntu-desktop-regression.json)

## Paquetes de revisión de `a3026d2`

| Sistema | Contenido | Paquete de Actions |
| --- | --- | --- |
| Windows x64 | Portable `.exe`, instalador `.exe`, fuente `.zip` y comprobantes. | [Descargar Windows](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45905864702/artifacts/15158955828) |
| Linux x86_64 | Portable `.tar.gz`, instalador `.run` y comprobantes. | [Descargar Linux](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45905864702/artifacts/15158945033) |

La revisión comparó el SHA-256 de cada ZIP de Actions y de cada archivo interno con su recibo. El ZIP de fuentes identifica el mismo commit que los instaladores y portables. Las pruebas de distribución de ambos sistemas aprobaron la actualización aislada desde 2.0.0, la conservación de la sesión y el rechazo de una descarga alterada. Ambos sistemas aprobaron también los controles de recursos y cancelación. Los artefactos de Actions tienen retención hasta el 3 de diciembre de 2026. [Notas de 2.2.0 Preview](PREVIEW_NOTES.md) · [Recibo de paquetes](evidence/candidate-a3026d2/verified-package-receipt.json) · [SHA-256](evidence/candidate-a3026d2/SHA256SUMS-2.2.0-CANDIDATE.txt)

## Dictámenes vigentes

| Decisión | Dictamen | Condición para reconsiderarlo |
| --- | --- | --- |
| Cierre técnico de Fase 04 | **NO-GO** | Completar Windows nativo a 150 % y 200 %, resolver o delimitar el recorte observado al 200 % con Qt y registrar el escritorio Linux. |
| Preparación técnica para Fase 05 | **NO-GO** | Completar el Quality Gate de Fase 04 y revisar la continuidad. El inicio requiere autorización específica. |
| Distribución pública de la Preview | **NO-GO** | Completar el Quality Gate y obtener autorización para publicar, etiquetar y firmar. Stable/LTS conserva la familia 2.0.x. |

Los ensayos de actualización usan manifiestos de prueba y el seguimiento E-04 conserva su tratamiento independiente. La aprobación funcional del propietario se registra por separado de la matriz. [Expediente de cierre](PHASE_04_CLOSEOUT.md) · [Protocolo real](VALIDATION_MATRIX.md#protocolo-de-escritorio-real) · [Riesgos residuales](RESIDUAL_RISK_REGISTER.md) · [Política de entregas](../RELEASE_POLICY.md).
