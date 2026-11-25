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
