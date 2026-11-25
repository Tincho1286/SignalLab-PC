# Matriz de validación de estabilización

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
