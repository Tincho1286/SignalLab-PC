# Puerta de calidad de Engineering Core

Dictamen vigente en la [continuidad de Fase 02C del 25/11/2026](#continuidad-de-fase-02c--25112026). El apartado inicial conserva el dictamen del candidato histórico `459b9fc`.

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

## Continuidad de Fase 02C · 25/11/2026

Candidato **`faef335bb7892cda92edc50a7c4f417a89b0415c`**, versión de auditoría **2.0.1**, en `develop`. La corrida 45673548563 aprobó los cuatro trabajos en Windows y Ubuntu con el mismo SHA limpio. Cada plataforma completó 890 pruebas integrales y 150 casos preventivos, sin fallos, errores ni omisiones. [Matriz y artefactos](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45673548563) · [Evidencia registrada](evidence/ci-faef335.json)

| Dictamen | Estado | Motivo |
| --- | --- | --- |
| Cierre de Engineering Core | **NO-GO** | E-06c–j alcanzaron los objetivos. Las líneas y ramas de la aplicación siguen por debajo de los objetivos de E-06a y E-06b. Quedan pendientes las condiciones de dependencias, alcance del lector y cuotas numéricas, y las actas de escritorio. |
| Preparación para Fase 03 | **NO-GO** | El contenedor opcional preserva proyectos con menos costo. El escenario de comunicaciones de 48 corridas sigue fuera del perfil medido y el cierre del Core continúa abierto. Se requiere una autorización separada para iniciar Fase 03. |
| Distribución pública | **NO-GO** | La actualización aislada desde 2.0.0 y los portables pasaron en los dos sistemas. E-04 mantiene firma Windows y validación del canal público como condiciones independientes. También sigue abierto E-01. |

### Resultado del trabajo

- Los ocho módulos con excepción de ramas cumplieron. La cobertura global llegó a 78,67 % de líneas y 64,60 % de ramas en Windows y a 78,61 % y 64,59 % en Ubuntu. Los objetivos permanecen en 85 % y 75 %. La configuración y alcance de instrumentación se mantuvieron. [Cobertura y brecha](../testing/FINAL_COVERAGE_REPORT.md)
- El lector MAT funciona en un proceso con cuota del SO y plazo. El resto del Core conserva memoria estimada y cancelación cooperativa. Se midieron perfiles con hasta 1 048 576 muestras, concurrencia de admisión y costo de persistencia. [Envolvente](../resources/OPERATIONAL_ENVELOPE.md) · [Revisión de seguridad](../security/DEPENDENCY_CONTINUATION.md)
- El proyecto científico opcional mantiene compatibilidad JSON y respaldo atómico. Con dos registros de 262 144 muestras, ocupó 8,39 MB frente a 46,49–48,59 MB en JSON. El destino se preserva si se cancela la escritura. La sesión recupera resultados CAS publicados. La hoja activa, sus variables y borradores quedan en memoria. [Dimensionamiento y alcance CAS](../persistence/COMMUNICATIONS_STORAGE_SIZING.md)
- En Windows real, a 96 DPI, se verificaron navegación, Welch, figura independiente, informe y reapertura de proyecto en ventana compacta. Los perfiles de CI amplían resolución y escala simulada. E-05 precisa las actas pendientes de Linux real y DPI del sistema. [Acta y protocolo](../gui/DESKTOP_CONTINUATION.md)

### Decisiones individuales pendientes

1. **E-01, Qt y OpenJPEG.** Decidir si se mantiene condicionada cualquier consideración de distribución a ruedas corregidas y revalidadas, o si se evalúa explícitamente un alcance limitado con la exposición documentada.
2. **E-02, HDF5.** Decidir si el importador local con cuota y validación cubre el uso autorizado durante la espera de una rueda corregida. La aprobación, si se da, debe delimitar los archivos y usuarios admitidos.
3. **E-03, recursos.** Confirmar la envolvente medida para el alcance evaluado, o especificar qué operación nativa requiere un plazo o una cuota forzada adicionales.
4. **E-04, distribución.** Mantener separadas la aceptación técnica del salto local y la decisión de firma y canal público. Este expediente sólo verifica el transporte en un entorno de auditoría.
5. **E-05, escritorio.** Aportar las actas del protocolo en un entorno real disponible o definir expresamente el alcance de resolución y DPI aceptado.

E-06a y E-06b siguen como deuda de pruebas. El saldo medido y las rutas prioritarias están detallados para su continuación en 02C. Ninguna excepción quedó aceptada por este informe. [Registro de excepciones](EXCEPTION_APPROVAL_REGISTER.md) · [Riesgos](RESIDUAL_RISK_REGISTER.md)
