# Quality Gate final de Fase 03

**Candidato 2.1.0 Preview · `441f1c2fcd9716d12ca3262a6b49728536f92435`.** Windows y Ubuntu ejecutaron la matriz sobre el mismo checkout limpio. La corrida terminó en el primer intento para este SHA. Se verificaron los hashes de los cinco archivos de evidencia y se recalcularon ambos Quality Gates localmente. Los dos informes coincidieron con los de CI. [Ejecución](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45834151197) · [Recibo de evidencia](evidence/candidate-441f1c2/matrix-receipt.json)

## Suite y cobertura

| Control | Objetivo | Windows Server 2022 | Ubuntu 22.04 |
| --- | ---: | ---: | ---: |
| Pruebas integrales aprobadas | Suite completa | 1 184 | 1 184 |
| Casos matemáticos preventivos | 150 | 150 | 150 |
| Pruebas de comunicaciones dentro de la suite | ≥64 | 67 | 67 |
| Cobertura global de líneas | ≥85 % | 88,95 % · 40 685/45 738 | 88,89 % · 40 656/45 738 |
| Cobertura global de ramas | ≥75 % | 75,92 % · 13 077/17 224 | 75,89 % · 13 072/17 224 |
| Mínimo de líneas entre los diez componentes de Fase 03 | ≥90 % | 97,92 % · barridos | 96,25 % · barridos |
| Mínimo de ramas entre los diez componentes de Fase 03 | ≥85 % | 87,50 % · CLI | 87,50 % · CLI |

Se conserva la configuración de cobertura de Engineering Core. Los componentes designados de 02C también alcanzaron sus objetivos. El verificador de Fase 03 aprobó los once controles de cada plataforma. La revisión del candidato indica cero defectos P0 abiertos y cero P1 internos sin resolver dentro del alcance probado. [Informe automatizado de Fase 03](evidence/candidate-441f1c2/quality-gate-03.json) · [Informe del Core](evidence/candidate-441f1c2/quality-gate-core.json) · [Matriz de validación](VALIDATION_MATRIX.md)

## Función científica, ejecución y compatibilidad

Se verificaron las operaciones y el enlace integrado desde GUI, Python y CLI, incluidas la ejecución sin Qt y la reutilización de reloj, unidades y procedencia. Los oráculos incluyen cuadratura de RC/RRC, conteo de errores, probabilidades de regiones QAM y 32 réplicas QPSK con ISI y AWGN. Preservaron sus contratos las sesiones históricas, diagramas, ROC, CAS y señales binarias. Los barridos reabren las corridas archivadas y rechazan contenido alterado. [Auditoría matemática](MATHEMATICAL_AUDIT.md) · [Trazabilidad](TRACEABILITY_MATRIX.md)

El enlace de 65 536 símbolos tardó 0,247 s en Windows y 0,249 s en Linux sin Qt. Los picos fueron 202,46 y 222,73 MiB. La cancelación FIR se observó en 51,59 y 44,58 ms. En la prueba del escritorio el intervalo máximo del bucle de eventos fue inferior a 65 ms en ambos runners. Se mantienen el carácter cooperativo de la cancelación, los presupuestos estimados y el seguimiento de tamaños fuera de los perfiles medidos. [Rendimiento y envolvente](PERFORMANCE_REPORT.md)

Se abrió el laboratorio en el escritorio Windows a 96 DPI, con ensayos adicionales de escala Qt. En 1366 × 768 a escala 2, el área lógica queda por debajo de la altura mínima de Workbench y el gráfico aprovecha el modo «Solo figura». Linux aprobó las pruebas automatizadas del laboratorio y las comprobaciones nativas de instalación. La revisión funcional del laboratorio sobre un escritorio Linux queda para la validación de Preview. [Acta de escritorio](VALIDATION_MATRIX.md#comprobación-del-escritorio-windows)

## Paquetes, integridad y seguridad

Se verificaron los dos portables, los dos instaladores, el archivo de fuentes y los cuatro comprobantes. Los ZIP de Actions coincidieron con sus hashes de origen. Cada adjunto coincidió por tamaño y SHA-256 con el comprobante del mismo candidato. La comprobación del ejecutable empaquetado incluye la ejecución del enlace y la reapertura de su archivo. [Sumas del candidato](evidence/candidate-441f1c2/SHA256SUMS-2.1.0-CANDIDATE.txt) · [Recibo de paquetes](evidence/candidate-441f1c2/verified-package-receipt.json)

| Plataforma | Archivos construidos por el candidato |
| --- | --- |
| Windows x64 | Portable `.exe`, instalador `.exe`, fuentes y comprobantes. [Paquete de Actions](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45834151197/artifacts/15127022665) |
| Linux x86_64 | Portable `.tar.gz`, instalador `.run` y comprobantes. [Paquete de Actions](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45834151197/artifacts/15127476322) |

Los artefactos binarios de Actions tienen retención hasta el 3 de diciembre de 2026. La actualización de 2.0.0 a 2.1.0 conservó los datos del usuario en las instalaciones de ensayo. Los manifiestos de prueba verificaron firma, hash y separación de canal. Qt 6.12.1, la compilación de Pillow sin JPEG 2000 y el origen de OpenSSL de Ubuntu quedaron registrados. E-04 continúa como seguimiento independiente. [Seguridad](SECURITY_REVIEW.md) · [SBOM Windows](evidence/candidate-441f1c2/windows-native.cdx.json) · [SBOM Linux](evidence/candidate-441f1c2/linux-native.cdx.json)

## Dictámenes independientes

| Decisión | Dictamen | Justificación |
| --- | --- | --- |
| Cierre técnico de Fase 03 | **GO** | Matriz integral, cobertura, referencias independientes, recursos, compatibilidad, cancelación y empaquetados aprobados. Riesgos residuales delimitados. |
| Preparación técnica para Fase 04 | **GO condicionado** | El enlace AWGN documentado sirve de control. La continuidad requiere validación funcional del propietario y autorización expresa para integrar y, posteriormente, iniciar la fase. |
| Preparación para distribución pública | **GO condicionado** | Están preparados los binarios, las fuentes, notas, checksums y procedencia. La etiqueta, el manifiesto público firmado y la prerelease requieren autorización expresa del propietario. Stable/LTS 2.0.x tiene su canal propio. |

El expediente se archiva en `develop`. El candidato conserva el SHA `441f1c2fcd9716d12ca3262a6b49728536f92435`. [Informe de cierre](PHASE_03_CLOSEOUT.md) · [Riesgos residuales](RESIDUAL_RISK_REGISTER.md) · [Política de publicación](../RELEASE_POLICY.md)
