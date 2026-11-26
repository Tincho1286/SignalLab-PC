# Informe del Quality Gate de Fase 04

**Estado en revisión.** La matriz de 2.2.0 Preview sobre `2a0a3fd97e63bd766d09739d51dc9aab4e9e6efb` terminó con Ubuntu cancelado. Se conservan los resultados de Windows y los recibos de distribución de ambas plataformas para esa revisión. [Matriz de Actions](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45899563971) · [Recibo](evidence/candidate-2a0a3fd/matrix-receipt.json)

## Evidencia disponible

| Control | Resultado | Evidencia |
| --- | --- | --- |
| Ciencia e interoperabilidad | Los contrastes independientes de Clarke, fase Rician y canales deterministas cumplieron sus tolerancias. El caso común de Workbench, Python y CLI conserva muestras, reloj, huellas y métricas. | [Auditoría](MATHEMATICAL_AUDIT.md) · [Paridad](evidence/candidate-2a0a3fd/windows-interface-parity.json) |
| Suite integral y cobertura | Windows aprobó 1 254 pruebas, los 150 casos preventivos y los umbrales globales y de componentes críticos. Ubuntu registró un fallo en el barrido del Workbench y agotó el plazo del runner durante el cierre. | [Resultado de Windows](evidence/candidate-2a0a3fd/windows-integral-receipt.json) · [Registro de Ubuntu](evidence/candidate-2a0a3fd/ubuntu-integral-tail.txt) · [Control automatizado](evidence/candidate-2a0a3fd/automated-gate-45899563971.json) |
| Recursos | Ambos runners midieron los tres perfiles exigidos, verificaron los archivos reabiertos y cumplieron límites de cancelación y respuesta offscreen. | [Tiempo, memoria y cancelación](PERFORMANCE_REPORT.md) |
| Paquetes | Instalador, portable, comprobantes y fuente verificados contra SHA-256. El enlace empaquetado y la actualización aislada desde 2.0.0 pasaron en ambos sistemas. | [Recibo](evidence/candidate-2a0a3fd/verified-package-receipt.json) · [Hashes](evidence/candidate-2a0a3fd/SHA256SUMS-2.2.0-CANDIDATE.txt) · [Seguridad](SECURITY_REVIEW.md) |
| Escritorio real | Windows a 100 % verificó enlace, guardado, regreso al catálogo y figura de distribuciones. Restan las comprobaciones nativas indicadas en el protocolo. | [Protocolo y registro](VALIDATION_MATRIX.md) |

### Cobertura de la matriz

| Plataformas | Líneas globales | Ramas globales | Mínimo de líneas críticas | Mínimo de ramas críticas |
| --- | ---: | ---: | ---: | ---: |
| Objetivos | 85 % | 75 % | 90 % | 85 % |
| Windows Server 2022 | 89,22 % · 43 178/48 393 | 76,29 % · 13 741/18 012 | 94,08 % | 85,00 % |
| Ubuntu 22.04 | Sin medición | Sin medición | Sin medición | Sin medición |

El informe de Windows se generó sobre un checkout limpio de `2a0a3fd`. Al combinar la instrumentación se identificaron 173 archivos de cobertura generados por procesos simbólicos. La prueba de reutilización de una respuesta en el CAS, que había excedido la espera anterior en la exploración local, aprobó en la matriz. [Línea base](evidence/candidate-2a0a3fd/windows-baseline.json) · [Recibo integral](evidence/candidate-2a0a3fd/windows-integral-receipt.json)

La espera de la prueba retenía el intérprete mientras el barrido avanzaba en un hilo de Qt. Al vencer su plazo, el cierre de la ventana con un cálculo activo podía mostrar un diálogo modal sin respuesta en el runner. La espera ahora alterna el procesamiento de eventos con una pausa que deja avanzar al trabajador Python. La limpieza cancela y espera los trabajos activos antes de cerrar. Los límites de espera de la prueba, las aserciones de resultados y los umbrales de cobertura se conservan. La repetición focalizada en Ubuntu usa la instrumentación de la matriz. [Investigación](IMPLEMENTATION_LOG.md#diagnóstico-del-barrido-en-ubuntu)

## Paquetes de revisión

| Sistema | Contenido | Paquete de Actions |
| --- | --- | --- |
| Windows x64 | Portable `.exe`, instalador `.exe`, fuente `.zip` y comprobantes. | [Descargar Windows](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45899563971/artifacts/15156258546) |
| Linux x86_64 | Portable `.tar.gz`, instalador `.run` y comprobantes. | [Descargar Linux](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45899563971/artifacts/15155098928) |

La revisión compara el hash de cada ZIP de Actions con su recibo de origen y vuelve a calcular el hash de cada archivo interno. El ZIP de fuentes identifica el mismo commit candidato. El portable Windows incluye la licencia y los avisos embebidos. El portable Linux conserva la licencia, los avisos y el manifiesto del entorno. Los artefactos de Actions tienen retención hasta el 3 de diciembre de 2026. [Notas de 2.2.0 Preview](PREVIEW_NOTES.md) · [Recibo de paquetes](evidence/candidate-2a0a3fd/verified-package-receipt.json)

## Dictámenes vigentes

| Decisión | Dictamen | Condición para reconsiderarlo |
| --- | --- | --- |
| Cierre técnico de Fase 04 | **NO-GO** | Verificar en Ubuntu el arreglo de la prueba y calificar la revisión corregida en la matriz. Completar el escritorio real. |
| Preparación técnica para Fase 05 | **NO-GO** | Completar la revisión de Fase 04 y emitir el dictamen de continuidad sobre los resultados consolidados. Su inicio requiere autorización específica. |
| Distribución pública de la Preview | **NO-GO** | Completar el Quality Gate. La publicación, la etiqueta y las claves de producción requieren autorización separada. Stable/LTS conserva su canal 2.0.x. |

Los ensayos de actualización usan manifiestos de prueba y el seguimiento E-04 conserva su tratamiento independiente. La aprobación funcional del propietario se registra por separado de la matriz. [Riesgos residuales](RESIDUAL_RISK_REGISTER.md) · [Política de entregas](../RELEASE_POLICY.md).
