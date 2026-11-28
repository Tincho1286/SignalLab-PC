# Entrega técnica de Fase 06

**2.4.0 Preview** quedó publicada desde `develop` para el candidato `1eb462e24034a9c7f41183b4da4654334460d07c`. [Descargas](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.4.0) · [Quality Gate](QUALITY_GATE_REPORT.md)

La arquitectura agrega un modelo multipuerto independiente de Qt, un servicio común de solicitudes, archivos Touchstone y persistencia RF de proyecto. Se reutilizaron Transfer, Signal, propagación, el contexto de ejecución y Monte Carlo. Los métodos, límites y referencias están en el [catálogo de integración](INTEGRATION_CATALOG.md) y los [contratos científicos](SCIENTIFIC_CONTRACTS.md).

| Dictamen | Resultado |
| --- | --- |
| Calificación científica | Aprobada para los modelos acreditados y contrastes independientes A–F. |
| Calificación técnica | Aprobada por el Gate acumulado de ambos sistemas. |
| Distribución Preview | Aprobada con portables e instaladores, código fuente, manifiesto firmado, inventario, SBOM y huellas. |
| Aceptación funcional | Pendiente de la revisión del propietario. |
| Integración en main | Pendiente de autorización expresa. |
| Continuidad hacia Fase 07 | Preparada para evaluación tras la aceptación. Su ejecución requiere autorización específica. |

El verificador público confirmó el canal Preview 2.4.0 y la base Stable/LTS 2.0.0. Los instaladores se probaron con el salto aislado desde la LTS, conservación de sesión y rechazo de la descarga alterada. [Publicación](evidence/candidate-1eb462e/publication.json) · [Comprobantes](evidence/candidate-1eb462e/verified-build.json)

Los alcances de ondas, modelos cúbicos, formatos y cancelación siguen en el [registro de límites](TECHNICAL_DEBT_REGISTER.md). [Revisión funcional](FUNCTIONAL_ACCEPTANCE.md)
