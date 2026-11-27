# Matriz de validación de SignalLab Engineering

## Criterios vigentes

El Quality Gate de expansión rige las fases autorizadas hasta la 10. Cada fase agrega oráculos y controles por dominio antes de ejecutar sus pruebas. La matriz se evalúa en Windows y Linux sobre **el mismo SHA limpio**, con resultados por plataforma y requisitos trazables.

| Control | Evidencia mínima |
| --- | --- |
| Cobertura global | ≥85 % de líneas y ≥75 % de ramas en cada plataforma. |
| Componentes críticos | ≥90 % de líneas y ≥85 % de ramas por componente crítico. Inventariar los componentes antes de medir y justificar exclusiones. |
| Defectos y regresiones | Cero P0 y cero P1 internos sin resolver. Pruebas con resultados observables en motores y recorridos viejos y nuevos. |
| Validación matemática | Oráculos independientes y tolerancias fijadas antes de medir. Identidades, casos límite, errores y contraste simbólico, numérico o estadístico según el dominio. |
| Compatibilidad e integridad | Carga histórica, conservación de unidades/reloj/condiciones, procedencia, integridad, atomicidad y recuperación. |
| Reproducibilidad | Solicitudes, parámetros, fuentes, huellas, versiones, semillas y rutas auditables. Contrastar resultados entre interfaces cuando compartan una operación. |
| Seguridad y recursos | Revisar dependencias, formatos externos y límites del perfil. Medir memoria, tiempo, concurrencia, cancelación y recuperación. Distinguir estimaciones de cuotas estrictas. |
| Interfaz | Pruebas automatizadas funcionales en Windows y Linux. Incluir entrada, cambio de método, cálculo, errores, resultados, gráficos y reuso donde aplique. |
| Distribución | Instaladores, portables, fuentes, inventarios, procedencia, hashes y manifiesto firmado comprobados. Verificar separación Stable/LTS y Preview. |
| Documentación | Requisitos, contratos, causas de defectos, casos, resultados, riesgos y SHA. Registrar por separado el dictamen técnico, la aceptación funcional y el permiso de integración. |

Las comprobaciones específicas a 100 %, 125 %, 150 % y 200 %, las matrices DPI, resoluciones físicas, monitores múltiples y los escritorios Linux manuales pasan a ser evidencia diagnóstica y de seguimiento. Los fallos funcionales conocidos y las regresiones automatizadas conservan su tratamiento por severidad. La aceptación funcional corresponde al propietario después de publicar la Preview. [Gates A, B y C](RELEASE_POLICY.md#de-una-fase-autorizada-a-su-cierre) · [Protocolo de interfaz](UX_DESIGN_PRINCIPLES.md#comprobar-el-recorrido)

## Calificación de Fase 11

La calificación definitiva eleva a ≥99 % las líneas, ramas y funciones globales, y las líneas y ramas de componentes críticos. El protocolo fija el inventario de funciones, denominadores, exclusiones justificadas y reconciliación por plataforma antes de medir. La cobertura complementa oráculos independientes y pruebas que comprueban resultados. Mantener métricas auditables y resolver en cada fase los defectos que le corresponden. [Paquetes y dictámenes de Fase 11](ROADMAP.md#fase-11--consolidación-y-calificación-definitiva)

## Matriz histórica de estabilización

**Estados** verificado, corregido y verificado, mitigado parcialmente, pendiente, bloqueado y no aplicable. El [informe de línea base](BASELINE_REPORT.md) identifica la revisión exacta de cada prueba.

| Criterio | Evidencia | Estado |
| --- | --- | --- |
| WP-01 · Integridad de la referencia | Revisiones separadas, scripts de reproducción y matriz Windows/Linux | Verificado en ambos sistemas sobre el mismo SHA, incluida la suite, cobertura y diagnóstico de los portables. |
| WP-02 · DFT, DTFT e IDFT | Suma compleja independiente, orígenes positivos/negativos, gran magnitud, N par/impar, exportación y recuperación de reloj | Corregido y verificado en Windows/Linux. |
| WP-02 · Estudio de ventanas | Inversión de ambos formatos de salida para N=5 y N=6, con ceros agregados | Corregido y verificado en Windows/Linux. |
| WP-03 · Inventario de portables 2.0.0 | CArchive y SHA-256 reales para Windows y Linux, correlación con CPython y Qt | Verificado para los dos runtimes. Versiones de demás DLL/SO pendientes. |
| WP-03 · Qt SVG | Códec acotado en 2.0.0 y migración Qt candidata. Portables descartables de Windows y Linux | Mitigado parcialmente en 2.0.0. Versión corregida para este aviso y verificada en los portables candidatos. |
| WP-03 · CPython | Paquete Windows oficial con firma y hash, verificación de la biblioteca incluida y del runtime cargado en ambos binarios | Actualizado y verificado a 3.14.10 en Windows/Linux sobre `ccb6a86`. El paquete Linux conserva la versión base de OpenSSL 3.0.2. |
| WP-03 · Tamaño de MATLAB | El archivo `.m` se rechaza antes de la lectura si requiere más memoria que la estimada disponible | Corregido y verificado en Windows/Linux. |
| WP-03 · Plazos y escalas | Cancelación cooperativa y terminación del worker auditadas. Límites y exposición documentados | Mitigado parcialmente. Presupuesto común y perfiles de estrés pendientes. |
| WP-04 · Líneas y ramas | `coverage.py` sobre suite completa. Datos de proceso y métricas por motor | Medición verificada en ambos sistemas. Muestreo y Fourier alcanzan el 90 % orientativo de líneas. El objetivo global sigue abierto. |
| WP-02/WP-04 · Referencias nuevas | 17 pruebas de Muestreo y Fourier. Incluyen puntos medios de cuantización y energía con escala extrema | Corregido y verificado en Windows/Linux. |
| WP-05 · Apertura, migración y guardado | Sesiones creadas con los escritores 1.9.3, 1.9.4 y 2.0.0. Resultados, relaciones y relojes comprobados | Verificado en Windows/Linux para esas rutas históricas. |
| WP-05 · Recuperación y corrupción | Pruebas de escritura interrumpida y rechazo de referencias inválidas | Verificado en Windows/Linux en el perfil offscreen. |
| WP-06 · Grafo y ADR | AST, componentes cíclicos y evaluación de las representaciones. Un flujo piloto definido | Verificado para el grafo. ADR propuesto. |
| Distribución 2.0.0 | Validación nativa de instaladores y manifiestos de la estable | Verificado para el SHA del release. |
| Distribución del candidato | Instaladores reales y descarga verificada con manifiesto descartable en `853bd67` | Verificado en Windows y Ubuntu en CI. La actualización desde el canal público y la confianza Authenticode requieren validación de entrega. |
| Fase 02 y laboratorios nuevos | Implementación de la arquitectura objetivo | No aplicable a la autorización de Fase 01. |

## Controles del candidato de cierre

| Control | Resultado y alcance |
| --- | --- |
| SBOM nativo | 219 archivos PE de Windows y 391 ELF de Linux identificados por huella y origen. Se registraron 42 enlaces de Linux. |
| OpenSSL Linux | `libssl.so.3` y `libcrypto.so.3` coinciden con la revisión corregida de Ubuntu `3.0.2-0ubuntu1.30`. |
| Qt | 6.12.0 verificado en ambos portables. Evaluación de 6.12.1 pendiente de las ruedas compatibles de PySide6 Essentials y shiboken6. |
| Recursos | DFT, DTFT y cambio de tasa medidos en ambos sistemas. La guarda de memoria cruza el límite previsto y tanto la DTFT como el worker simbólico cancelan. Plazos y cuotas universales pendientes. |
| Proyectos, diagramas, ROC y CAS | Se amplió la suite con oráculos, reutilización y compatibilidad de esquemas. El estado completo de una hoja CAS queda fuera de la persistencia de sesión. |
| UI y DPI | Cuatro tamaños y tres escalas Qt revisados visualmente. Interacción de Muestreo y CAS en Windows. Capturas X11 sobre Xvfb en Ubuntu. Migración entre monitores y escritorio Linux interactivo pendientes. |

[Informe de cierre](PHASE_01_CLOSEOUT.md) · [Evidencia de distribución](evidence/phase-01-distribution-853bd67.json)

La validación de Engineering Core se registra en la [matriz de Fase 02B](phase_02b/PHASE_02B_TRACEABILITY_MATRIX.md) y conserva por separado la evidencia histórica de estabilización.

La [matriz del candidato 02C](phase_02c/validation/FINAL_VALIDATION_MATRIX.md) incorpora pruebas de procedencia y escala, cancelación de persistencia, instaladores, SBOM, recursos y evidencia visual por entorno.

### Continuación autónoma de 02C

La matriz por SHA conserva la línea base de 890 pruebas por sistema, la corrida de 907 con portables y actualización y los candidatos siguientes. La cobertura, los benchmarks, el SBOM y los perfiles de escritorio se evalúan en sus alcances respectivos. [Matriz vigente](phase_02c/validation/FINAL_VALIDATION_MATRIX.md#continuación-autónoma)
