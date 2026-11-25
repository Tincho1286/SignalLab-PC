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
