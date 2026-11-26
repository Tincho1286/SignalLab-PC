# Puerta de calidad de Engineering Core

Dictamen vigente en [Evaluación del candidato 623c9dd](#evaluación-del-candidato-623c9dd). Los apartados de versiones anteriores conservan sus dictámenes históricos.

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
| Cierre de Engineering Core | **NO-GO** | El candidato pasó las suites y los mínimos críticos. Quedan los objetivos globales de líneas y ramas y la evidencia de escritorio físico pendiente. |
| Preparación técnica para Fase 03 | **NO-GO** | La escala sintética está verificada por lotes. Antes de iniciar cualquier fase posterior corresponde cerrar el Core y obtener autorización específica. |
| Distribución pública | **NO-GO** | Portables, instaladores y salto aislado desde 2.0.0 verificados en ambos sistemas. Firma Windows, canal público y exposición nativa conservan sus propios criterios. |

### Cambios verificados y mediciones

- La matriz de `eb50895250b124ec0554a4c52d894d5ac790e7a5` pasó cinco trabajos de CI, 925 pruebas integrales y 150 casos preventivos por sistema. De los 37 criterios automáticos por plataforma, pasaron 35. Los dos restantes son los objetivos globales de cobertura. En Windows se midió 81,82 % de líneas y 67,07 % de ramas. En Linux, 81,76 % y 67,05 %. La reproducción local del Quality Gate devolvió código 1 con `--require-automated`, tal como exige la cobertura medida. [Corrida completa](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45689459348) · [Evidencia consolidada](evidence/ci-eb50895.json)
- El supervisor completó las 345 pruebas de interfaz de los dos empaquetados, sin timeout. En Windows tomó 555,8 s y en Linux 506,9 s. Los instaladores verificaron 2.0.0 → 2.0.1 con clave temporal, sustitución en el mismo destino, preservación de sesión y rechazo de descarga dañada. El flujo automático posterior ejecutó sólo matemática y estática y pasó en ambos sistemas. Se canceló una auditoría intermedia superada y quedó su historial. [Flujo rápido](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45691896234) · [Auditoría cancelada](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45689038376)
- La matriz completa de `54adaa0` validó 907 pruebas integrales y 150 casos preventivos por sistema. SLPROJ subió de 86,11 % de líneas y 64,00 % de ramas en la referencia a 95,28 % y 89,13 %. En `99f7ce2` pasaron 922 pruebas y 150 casos preventivos en cada sistema y todos los componentes críticos alcanzaron sus mínimos. La aplicación llegó a 81,35 % de líneas y 66,74 % de ramas en Windows y 81,29 % y 66,72 % en Linux. La distribución de ese SHA agotó el límite de la suite de interfaz. [Cobertura](../testing/FINAL_COVERAGE_REPORT.md) · [Evidencia por control](evidence/quality-gate-99f7ce2.json)
- Se verificaron 48 corridas, 288 registros, 75 497 472 muestras complejas y 1 208 085 276 bytes en `54adaa0`. El banco alcanzó 170,0 MiB de RSS en Windows y 176,9 MiB en Linux. Volvió a verificar siete corridas antes de reanudar la octava, que se había cancelado. La campaña usa proyectos completos independientes y un catálogo con hashes. [Dimensionamiento y campaña](../persistence/COMMUNICATIONS_STORAGE_SIZING.md)
- El mayor intervalo medido del temporizador de Qt pasó de 1 785,5 a 10,6 ms en Windows CI y de 1 788,2 a 10,7 ms en Linux CI al escribir SLPROJ en segundo plano. La medición usa dos registros de 262 144 muestras y tres repeticiones por modo. El mayor valor exploratorio en el equipo Windows local fue 29,3 ms para el escritor en segundo plano. [Recuperación](../resources/OPERATIONAL_ENVELOPE.md#recuperación-y-concurrencia-en-la-continuación-autónoma)
- CAS guarda su hoja, variables complejas y borrador en ambos formatos. Windows real confirmó la reapertura con la hoja enfocada tras corregir un conflicto con el método QWidget.window. Se agregaron regresiones de checkpoint obsoleto, permiso denegado, edición de polos y cálculo LTI fallido o cancelado. [Contrato CAS](../persistence/CAS_PERSISTENCE_VALIDATION.md) · [Acta Windows](../gui/DESKTOP_CONTINUATION.md) · [Causas y pruebas](../IMPLEMENTATION_LOG.md)
- NumPy 2.5.5 y SciPy 1.18.1 se verificaron con los portables e inventarios de ambos sistemas en `54adaa0`. El inventario Linux confirmó OpenSSL de Ubuntu `3.0.2-0ubuntu1.30`. El importador MAT conserva su cuota de SO y la admisión compartida. Permanecen los riesgos de proveedor y la cancelación cooperativa fuera de las fronteras medidas. [SBOM y avisos](../security/DEPENDENCY_CONTINUATION.md)

### Condiciones pendientes

E-06a y E-06b son tareas internas de pruebas. El verificador publica el déficit por archivo y por rama y exige los objetivos originales. E-01, E-02, E-04 y E-05 quedan delimitadas por dependencia, distribución o entorno de escritorio. Los 22 perfiles temporizados de E-03 confirmaron cancelación con integridad conservada en ambos sistemas. El comportamiento fuera de los tamaños probados y las llamadas nativas no acotadas conservan su propio alcance. El lector MAT aplica cuotas efectivas del SO. Ninguna condición residual se ha aceptado en nombre del mantenedor. [Registros](EXCEPTION_APPROVAL_REGISTER.md) · [Reanudación](#punto-de-reanudación)

### Punto de reanudación

1. Obtener los artefactos de la corrida vigente de [la matriz por SHA](FINAL_VALIDATION_MATRIX.md#continuación-autónoma). Verificar que ambos informes `baseline.json`, los benchmarks y los inventarios coinciden con el SHA de esa corrida. Registrar toda auditoría fallida antes de seleccionar otro candidato.
2. Ejecutar `python tools/check_quality_gate_02c.py --candidate <SHA> --input work/quality-input --output work/quality-gate --require-automated` con los cuatro artefactos descomprimidos por runner. El código de salida 1 identifica controles pendientes y el JSON los detalla.
3. En `coverage_priority` y el `coverage.json` de Linux, priorizar traspaso de señales y sistemas, diseño y comparación de filtros y acciones de tabla y sonda. Faltan 1 384 líneas y 1 305 ramas en Linux y 1 359 y 1 302 en Windows. El ensayo local de referencia biblioteca → DFT → IDFT está en `work/02c-autonomous-local/workflow_route_probe.py` y comprueba fase, origen, procedencia y retorno al resultado. Integrar estos flujos con casos de error y cancelación, medirlos de forma focal y agrupar la siguiente auditoría completa. El comando local de verificación es `python -B -X utf8 tools/check_engineering_baseline.py --output work/engineering-baseline` en un checkout limpio.

La evidencia histórica permanece versionada. Los recibos, SBOM, campaña y benchmark se vinculan desde el índice con SHA-256 de origen y de la copia normalizada. La referencia técnica es `eb50895`. Las modificaciones posteriores en `develop` sólo afectan la documentación y las condiciones que disparan CI. [Índice vigente](evidence/ci-eb50895.json) · [Índice de 54adaa0](evidence/ci-54adaa0.json)

## Avance local posterior a eb50895

Los ensayos focales sobre el código de desarrollo proyectan que el objetivo de líneas está cubierto y que quedan alrededor de 485 ramas para el 75 %. El expediente conserva los 35 de 37 controles automáticos aprobados en la última matriz por sistema. Los tres dictámenes anteriores permanecen abiertos hasta validar el mismo candidato en ambos sistemas y resolver las condiciones externas que les corresponden. Se reserva la ejecución completa en GitHub para el candidato que alcance ambos umbrales. [Medición ampliada](../testing/FINAL_COVERAGE_REPORT.md#medición-focal-de-la-siguiente-revisión)

La medición integral local de `8793c48` confirmó 85,52 % de líneas y 72,10 % de ramas en Windows con 1 039 pruebas y 150 casos preventivos aprobados. El déficit de ramas fue de 477. Esta evidencia amplía la validación local en modo offscreen. La matriz de ambos sistemas, las verificaciones de escritorio y el dictamen de distribución mantienen sus condiciones. [Medición integral local](../testing/FINAL_COVERAGE_REPORT.md#medición-integral-local-en-windows)

## Evaluación del candidato 623c9dd

El despacho 45739704501 evaluó `623c9ddcc2460485b549e864fa86ddc6b7cba407` en `develop`. Windows pasó 36 de 37 controles y Ubuntu 37 de 37. Se cotejaron los cinco artefactos con sus digests y el verificador local reprodujo el dictamen publicado por GitHub. [Matriz](FINAL_VALIDATION_MATRIX.md#resultado-de-623c9dd) · [Dictamen por control](evidence/quality-gate-623c9dd.json) · [Recibos y huellas](evidence/ci-623c9dd.json)

| Dictamen | Estado | Evidencia y criterio pendiente |
| --- | --- | --- |
| Cierre de Engineering Core | **Pendiente** | Los objetivos globales y de componentes se cumplieron en ambos runners. El control integral de Windows falló por una aserción de identidad de rutas. La corrección del test pasó localmente. E-01, E-02 y E-05 conservan seguimiento y decisión individual. |
| Preparación para Fase 03 | **Pendiente** | Pasaron la campaña de 48 corridas y los perfiles de cancelación y persistencia en ambos runners. La preparación requiere resolver el cierre del Core, acordar la envolvente admisible y obtener autorización específica. |
| Distribución pública | **Pendiente** | Se verificaron los portables, SBOM, instaladores y salto aislado de 2.0.0 a 2.0.1 en los dos sistemas. E-04 conserva la verificación de firma de producción y del canal público. |

En el trabajo Windows, `RUNNER~1` y `runneradmin` eran dos escrituras del mismo directorio temporal. El test comparaba las cadenas. `b6bcb85` cambió la comprobación a identidad del sistema de archivos y pasó 36 pruebas en Windows local. Relanzar el trabajo original conservaría el SHA que contiene la aserción anterior. [Causa y corrección](../IMPLEMENTATION_LOG.md) · [Trabajo Windows](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45739704501/job/139641392962)

La comprobación en Windows real a 96 DPI encontró que el selector de figuras podía desactivarse al maximizar. `87b74ed` corrigió el registro de figuras y pasó la comprobación en ese escritorio y 83 pruebas relacionadas. Los dos commits posteriores tienen evidencia focal separada de la matriz de `623c9dd`. [Acta de escritorio](../gui/DESKTOP_CONTINUATION.md#medidas-de-frecuencia-en-el-candidato-623c9dd)

El cotejo del inventario confirmó 219 archivos nativos de Windows y 389 de Linux. En Ubuntu se verificaron `libssl.so.3` y `libcrypto.so.3` de `libssl3` 3.0.2-0ubuntu1.30. El resultado de la prueba de actualización corresponde a una firma de auditoría. Las decisiones externas siguen abiertas en el registro de excepciones. [Dependencias](../security/DEPENDENCY_CONTINUATION.md) · [Excepciones](EXCEPTION_APPROVAL_REGISTER.md)

### Confirmación focalizada de las correcciones posteriores

Las tres regresiones se aprobaron en el runner Windows 2022 sobre `8e274e7`. La prueba que falló por el alias de ruta pasó con la corrección de identidad del sistema de archivos. También pasó la apertura de figuras tras cambiar de disposición. El dictamen integral conserva la corrida única de `623c9dd`. La evidencia focalizada confirma ambas correcciones y los dictámenes de cierre, preparación y distribución permanecen pendientes por sus criterios. [Pruebas del runner](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45744295852/job/139656507132) · [Alcance](FINAL_VALIDATION_MATRIX.md#regresiones-focalizadas-en-windows-sobre-8e274e7)
