# Puerta de calidad de Engineering Core

Dictamen vigente en la [continuación autónoma de Fase 02C](#continuación-autónoma-de-fase-02c). Los apartados anteriores conservan los dictámenes históricos de `459b9fc` y `faef335`.

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

## Continuación autónoma de Fase 02C

Referencia de partida `faef335bb7892cda92edc50a7c4f417a89b0415c`, expediente `7973a526dc202a7934adf5d3724c34f0c7d1d61c`. El candidato nuevo conserva la versión de auditoría 2.0.1. La [matriz por SHA](FINAL_VALIDATION_MATRIX.md#continuación-autónoma) registra los candidatos intermedios, el timeout de la auditoría Linux y la corrida a la que corresponde cada verificación.

| Dictamen | Resultado vigente | Condición |
| --- | --- | --- |
| Cierre de Engineering Core | **NO-GO** | El objetivo global de líneas y ramas sigue pendiente. Se requiere la medición integral del candidato vigente y completar la evidencia de escritorio real. |
| Preparación técnica para Fase 03 | **NO-GO** | La escala sintética está verificada por lotes. Antes de iniciar cualquier fase posterior corresponde cerrar el Core y obtener autorización específica. |
| Distribución pública | **NO-GO** | El salto aislado desde 2.0.0 funcionó en ambos sistemas en la matriz anterior. La validación del candidato vigente, la firma Windows, el canal público y la resolución de exposición nativa conservan sus propios criterios. |

### Cambios verificados y mediciones

- La matriz completa de `54adaa0` validó 907 pruebas integrales y 150 casos preventivos por sistema. SLPROJ subió de 86,11 % de líneas y 64,00 % de ramas en la referencia a 95,28 % y 89,13 %. La medición de aplicación de `3a68618` completó 917 pruebas y 150 casos preventivos en cada sistema, con 81,09 % / 66,61 % en Windows y 81,03 % / 66,59 % en Linux. El empaquetado Windows de esa corrida agotó el tiempo del verificador UI. [Cobertura](../testing/FINAL_COVERAGE_REPORT.md) · [Evidencia por control](evidence/quality-gate-3a68618.json)
- Se verificaron 48 corridas, 288 registros, 75 497 472 muestras complejas y 1 208 085 276 bytes en `54adaa0`. El banco alcanzó 170,0 MiB de RSS en Windows y 176,9 MiB en Linux. Volvió a verificar siete corridas antes de reanudar la octava, que se había cancelado. La campaña usa proyectos completos independientes y un catálogo con hashes. [Dimensionamiento y campaña](../persistence/COMMUNICATIONS_STORAGE_SIZING.md)
- El mayor intervalo medido del temporizador de Qt pasó de 1 785,5 a 10,6 ms en Windows CI y de 1 788,2 a 10,7 ms en Linux CI al escribir SLPROJ en segundo plano. La medición usa dos registros de 262 144 muestras y tres repeticiones por modo. El mayor valor exploratorio en el equipo Windows local fue 29,3 ms para el escritor en segundo plano. [Recuperación](../resources/OPERATIONAL_ENVELOPE.md#recuperación-y-concurrencia-en-la-continuación-autónoma)
- CAS guarda su hoja, variables complejas y borrador en ambos formatos. Windows real confirmó la reapertura con la hoja enfocada tras corregir un conflicto con el método QWidget.window. Se agregaron regresiones de checkpoint obsoleto, permiso denegado, edición de polos y cálculo LTI fallido o cancelado. [Contrato CAS](../persistence/CAS_PERSISTENCE_VALIDATION.md) · [Acta Windows](../gui/DESKTOP_CONTINUATION.md) · [Causas y pruebas](../IMPLEMENTATION_LOG.md)
- NumPy 2.5.5 y SciPy 1.18.1 se verificaron con los portables e inventarios de ambos sistemas en `54adaa0`. El inventario Linux confirmó OpenSSL de Ubuntu `3.0.2-0ubuntu1.30`. El importador MAT conserva su cuota de SO y la admisión compartida. Permanecen los riesgos de proveedor y la cancelación cooperativa fuera de las fronteras medidas. [SBOM y avisos](../security/DEPENDENCY_CONTINUATION.md)

### Condiciones pendientes

E-06a y E-06b son tareas internas de pruebas. El verificador publica el déficit por archivo y por rama y exige los objetivos originales. E-01, E-02, E-04 y E-05 quedan delimitadas por dependencia, distribución o entorno de escritorio. E-03 se evalúa sobre su envolvente de perfiles y presupuestos, con cuotas efectivas sólo en el lector MAT. Ninguna condición residual se ha aceptado en nombre del mantenedor. [Registros](EXCEPTION_APPROVAL_REGISTER.md) · [Reanudación](#punto-de-reanudación)

### Punto de reanudación

1. Obtener los artefactos de la corrida vigente de [la matriz por SHA](FINAL_VALIDATION_MATRIX.md#continuación-autónoma). Verificar que ambos informes `baseline.json`, los benchmarks y los inventarios coinciden con el SHA de esa corrida. Registrar toda auditoría fallida antes de seleccionar otro candidato.
2. Ejecutar `python tools/check_quality_gate_02c.py --candidate <SHA> --input work/quality-input --output work/quality-gate --require-automated` con los cuatro artefactos descomprimidos por runner. El código de salida 1 identifica controles pendientes y el JSON los detalla.
3. En `coverage_priority` y el `coverage.json` de Linux, priorizar el traspaso de señales y sistemas en `toolbox.py` y `workbench.py`, el diseño y la comparación de filtros en `course_tools_panel.py` y las acciones de tabla y sonda. Verificar datos que recibe y guarda cada herramienta, cancelar al iniciar o durante el trabajo y comprobar reapertura. Medir el resultado con `python -B -X utf8 tools/check_engineering_baseline.py --output work/engineering-baseline` en un checkout limpio. Mantener la cobertura total de líneas y ramas como criterio de cierre.

La evidencia histórica permanece versionada. Los recibos, SBOM, campaña y benchmark de cada matriz se vinculan desde el índice con SHA-256 de origen y de la copia normalizada. [Índice de 54adaa0](evidence/ci-54adaa0.json)
