# Trazabilidad

| Hallazgo | Requisito | Código, decisión o evidencia | Estado |
| --- | --- | --- | --- |
| C-01 y C-02 | C01 · Seguridad | `609c8c3`, [auditoría y mitigaciones](security/VULNERABILITY_REGISTER.md) | Excepciones de componentes e importación pendientes |
| C-04 | C02 · Matemática | `ef15207`, `c1bc5b2`, [oráculos](mathematics/INDEPENDENT_ORACLE_CATALOG.md) | Eje PSD corregido, validación en el candidato |
| C-03 | C03 · Procedencia | `8b1c63e`, `caf7bcd`, `459b9fc`, [ADR-003](contracts/ADR-003-VERIFIED-PROVENANCE.md), `test_math_provenance` | Corrección de asociaciones y reapertura |
| C-05 | C04 y C07 · Recursos y rendimiento | `b5ffa1d`, `825ecfb`, [envolvente](resources/OPERATIONAL_ENVELOPE.md) | Estimaciones y cancelación cooperativa, aceptación de alcance pendiente |
| C-06 | C05 · Persistencia | `924154a`, `459b9fc`, [integridad](persistence/PERSISTENCE_INTEGRITY_REPORT.md) | Formatos actuales comprobados, hojas CAS activas quedan pendientes |
| C-07 | C06 · Calidad | `c1bc5b2`, `459b9fc`, [cobertura](testing/FINAL_COVERAGE_REPORT.md) | El déficit que subsista requiere aceptación explícita |
| C-08 | C08 · GUI | `b036fd9`, [matriz visual](gui/GUI_VISUAL_VALIDATION_MATRIX.md) | Escritorio Windows y capturas, DPI del sistema y Linux real pendientes |
| C-09 | C09 · Distribución | `37ac1d4`, [comprobación de instaladores](distribution/INSTALLER_VALIDATION.md) | Evidencia aislada, entrega pública pendiente |
| C-10 | C10 y C11 · Arquitectura y cierre | `320030f`, [auditoría arquitectónica](architecture/FINAL_ARCHITECTURE_AUDIT.md) | Base headless comprobada, ampliación bajo autorización separada |

## Continuidad de 02C

| Excepción o requisito | Causa y corrección | Evidencia |
| --- | --- | --- |
| E-01, E-02 | Ruedas corregidas pendientes. Lector MATLAB clásico y HDF5 antes ejecutado dentro de la app. Aislamiento nativo en `8884ca5`. | [Revisión de componentes](security/DEPENDENCY_CONTINUATION.md), `test_math_input_integrity` y comprobación del portable |
| E-03 | El estimador Linux omitía cgroup v2. Se registra el presupuesto efectivo y se amplía la medición de tamaños, concurrencia y cancelación. | `8884ca5`, `faef335`, [envolvente](resources/OPERATIONAL_ENVELOPE.md) |
| C-06 | JSON duplicaba muestras en objetos Python y crecía por codificación decimal. Instantáneas compactas y formato opcional transaccional. | `8884ca5`, `faef335`, `test_math_project_archive`, [dimensionamiento](persistence/COMMUNICATIONS_STORAGE_SIZING.md) |
| E-04 | Ensayos previos no instalaban la versión estable pública antes del candidato. Se verifican el salto, la reapertura y la descarga rechazada. | `8884ca5`, `tools/check_stable_upgrade.py` y recibos de la matriz |
| E-05 | Etiqueta principal truncada en ventana compacta y Welch inicial incompatible con N = 64. Etiqueta accesible abreviada y segmento automático. | `faef335`, `test_desktop_session`, [acta y protocolo de escritorio](gui/DESKTOP_CONTINUATION.md) |
| E-06a–j | Brechas en precisión, procedencia, validación y traspaso entre herramientas. Casos preventivos y de integración con oráculos y resultados persistidos. | `8884ca5`, `faef335`, [cobertura por objetivo](testing/FINAL_COVERAGE_REPORT.md) |

## Continuidad autónoma y expedientes

| Hallazgo | Cambios y criterios | Prueba o evidencia |
| --- | --- | --- |
| C-05 · E-03 | Presupuesto compartido para cálculo, SLBIN, SLPROJ y el lector MAT | `test_math_project_archive.ProjectArchiveTests.test_parallel_calculation_and_archive_share_admission_and_release_on_error` y banco de recursos |
| C-06a | Contratos binarios documentados. Cabeceras finitas y rechazo antes de publicar. | `test_math_project_archive`, `test_math_scientific_storage` y casos de integridad |
| C-06b | Hoja CAS con estado versionado y referencias a registros ya publicados | `test_math_cas_session`, reapertura y cálculo posterior en `test_desktop_session` |
| C-06c | Recuperación binaria asíncrona, exclusión, cancelación y reintento | `test_desktop_session`, `tools/measure_recovery_responsiveness.py` |
| C-06d | Reapertura exacta por proyecto y retomado desde índice tras cancelar | `tools/measure_scientific_campaign.py` |
| C-08 | Flujo de edición de polos conserva multiplicidad. Convolución coincide en señal, inspector y CSV. | `test_desktop_session` |
| C-11 | Evaluación de integridad, cobertura y requisitos externos sin mezclar SHAs. | `tools/check_quality_gate_02c.py` y `test_engineering_quality_gate` |

| Hallazgo | Cadena de verificación de la continuación |
| --- | --- |
| C-03 · LTI | `99f7ce2` desplaza la publicación de entradas al resultado aceptado. `test_desktop_session` prueba cero de ganancia, realimentación singular y cancelación antes de reintentar. |
| C-05 · Cancelación | `3a68618` comprueba bloques de lectura JSON. `99f7ce2` extiende los perfiles a lecturas y MAT y comprueba integridad del destino. |
| C-06 · Recuperación | `0fc6d5a` preserva el foco CAS en escritorio y `3a68618` invalida checkpoints propios de otra generación. Las regresiones verifican datos reabiertos, permisos y exclusión. |
| C-07 · Cobertura | Casos de fase y reloj, cuantización, compensación, polos, tablas y sesión. El gate informa denominadores y pendientes por archivo. |
| C-09 · CI | Corrida 45684469040, timeout en verificador de interfaz Linux. `4f0f32d` mantiene las pruebas y renueva el presupuesto de supervisión. |
| C-02, C-03 y C-05 · Selección importada | `7f1babd` conserva referencias y reloj al incorporar, evita reabrir el archivo y hace participar a los lectores de metadatos del pool. Regresiones de selector real, proyecto histórico y admisión. |
| C-11 · Supervisor de pruebas | `eb50895` detecta progreso por prueba y conserva el tiempo total acotado. Un proceso real de ensayo termina correctamente al completar y se interrumpe si queda detenido. |
| C-04 · Control e invarianza | La realimentación y el lugar de raíces preservan el avance de H(z). La inversa por invarianza reconoce polos múltiples tras una reducción exacta. Oráculos en `test_math_lti_workflows` y `test_math_study_workflows`. |
| C-06 y C-07 · Escritorio y fórmulas | Reapertura de diagramas analógicos y digitales, filtros, procedencia de CAS, resultados de DFT y la interacción entre gráficos y tablas. Se suma la revisión de distribuciones y recurrencias con memoria. [Medición focal](testing/FINAL_COVERAGE_REPORT.md#medición-focal-de-la-siguiente-revisión) |

[Registro de causas y pruebas](IMPLEMENTATION_LOG.md) · [Evidencia y SHA](validation/FINAL_VALIDATION_MATRIX.md)
