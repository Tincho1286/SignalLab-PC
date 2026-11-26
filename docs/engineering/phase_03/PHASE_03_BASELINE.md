# Línea base de Fase 03

El árbol de entrada fue `f43bb1ccc96729acc17da1ce8329096b562fecb7` en `develop`. Cierre técnico acreditado en 02C. La matriz integral de `a80508c` aprobó 37 controles por plataforma. La auditoría focalizada de `64dc3c4` comprobó Qt 6.12.1, la exclusión de OpenJPEG y los instaladores. E-02, E-03 y E-05 tienen aprobación explícita. E-04 está abierto como seguimiento sin bloqueo de distribución. [Registro de 02C](../phase_02c/validation/QUALITY_GATE_REPORT.md#cierre-técnico-de-fase-02c) · [Decisiones](../phase_02c/validation/EXCEPTION_APPROVAL_REGISTER.md)

**SHA de referencia: `a5eafa9a1e98116e84b57d3bb0e8881ea02b2931`.** GitHub Actions verificó el mismo árbol limpio en Windows 2022 y Ubuntu 22.04 en un único despacho, primer intento, con `engineering_baseline=true`. El árbol desde `f43bb1c` difiere sólo en documentación de ingeniería. Se verificaron los cinco recibos de artefactos y el Quality Gate obtenido localmente coincidió con el publicado por CI. [Corrida](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45812233593) · [Recibos](evidence/baseline-a5eafa9-receipt.json) · [Quality Gate](evidence/baseline-a5eafa9-quality-gate.json)

| Medición | Windows 2022 | Ubuntu 22.04 |
| --- | ---: | ---: |
| Controles automatizados | 37/37 | 37/37 |
| Pruebas integrales | 1 110 | 1 110 |
| Casos preventivos | 150/150 | 150/150 |
| Cobertura de líneas | 37 996/43 001 (88,36 %) | 37 971/43 001 (88,30 %) |
| Cobertura de ramas | 12 438/16 544 (75,18 %) | 12 435/16 544 (75,16 %) |
| Archivos nativos con inventario | 218 | 385 |

E-06a–j conservan sus objetivos acreditados. Los dos portables aislados ejecutaron CPython 3.14.10 y Qt 6.12.1 con Pillow sin JPEG2000. Los SBOM de distribución coinciden con los inventarios y carecen de OpenJPEG. Los dos instaladores aprobaron el salto aislado desde 2.0.0 a 2.0.1, preservaron la sesión y rechazaron una descarga corrupta. El canal de ensayo empleó su firma temporal. [Evidencia por plataforma](VALIDATION_MATRIX.md)

La consolidación habilita la implementación funcional de Fase 03 en `develop`. Se mantienen los alcances aprobados de E-02, E-03 y E-05. E-04 permanece como seguimiento sin condicionar la distribución. [Decisiones del mantenedor](../phase_02c/validation/EXCEPTION_APPROVAL_REGISTER.md#seguimiento-de-e-04)
