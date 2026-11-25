# Puerta de calidad de Engineering Core

**NO-GO de cierre definitivo.** El candidato supera la matriz técnica en Windows y Linux. El criterio de cobertura global y varios objetivos de ramas del Core siguen pendientes. Los riesgos P1 que permanecen requieren resolución o aceptación individual, junto con la evidencia manual pendiente.

| Criterio | Dictamen de evidencia |
| --- | --- |
| 1–5 · P0, matemática, persistencia y procedencia | C-03 corregido. Los controles del alcance evaluado pasaron. Cuatro asuntos P1 conservan seguimiento en dependencias, MATLAB, recursos y distribución. |
| 6 · Cobertura | Todos los módulos designados superan 90 % de líneas. La cobertura global y las ramas indicadas requieren decisión individual. |
| 7–10 · Límites, compatibilidad, seguridad y rendimiento | Envolvente cooperativa y cancelación medida. Sesiones históricas aprobadas en los perfiles mantenidos. SBOM, avisos y benchmarks enlazados con el candidato. |
| 11–13 · Matriz, documentación y trazabilidad | Cuatro trabajos de CI aprobados en el mismo SHA. Las comprobaciones de sistema y entorno ajenas a CI conservan su alcance. |
| 14–15 · Riesgos y Fase 03 | Responsables y condiciones registradas. Capacidad técnica condicional dentro de la envolvente medida. |

Se excluyó de la matriz una corrida exploratoria local iniciada antes de la última corrección. Sus 865 pruebas terminaron sin fallos, pero la comprobación de fuentes detectó que cambió el árbol mientras corría. La referencia son los informes del candidato limpio de GitHub Actions.

[Informe integral](FINAL_VALIDATION_MATRIX.md) · [Cobertura por objetivo](../testing/FINAL_COVERAGE_REPORT.md) · [Riesgos](RESIDUAL_RISK_REGISTER.md) · [Registro de aprobaciones](EXCEPTION_APPROVAL_REGISTER.md)
