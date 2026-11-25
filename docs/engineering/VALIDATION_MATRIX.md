# Matriz de validación de estabilización

**Estados** verificado, corregido y verificado, mitigado parcialmente, pendiente, bloqueado y no aplicable. El [informe de línea base](BASELINE_REPORT.md) identifica la revisión exacta de cada prueba.

| Criterio | Evidencia | Estado |
| --- | --- | --- |
| WP-01 · Integridad de la referencia | Revisiones separadas, scripts de reproducción y matriz Windows/Linux | Verificado en ambos sistemas sobre el mismo SHA, incluida la suite, cobertura y diagnóstico de los portables. |
| WP-02 · DFT, DTFT e IDFT | Suma compleja independiente, orígenes positivos/negativos, gran magnitud, N par/impar, exportación y recuperación de reloj | Corregido y verificado en Windows/Linux. |
| WP-02 · Estudio de ventanas | Inversión de ambos formatos de salida para N=5 y N=6, con ceros agregados | Corregido y verificado en Windows/Linux. |
| WP-03 · Inventario de portables 2.0.0 | CArchive y SHA-256 reales para Windows y Linux, correlación con CPython y Qt | Verificado para los dos runtimes. Versiones de demás DLL/SO pendientes. |
| WP-03 · Qt SVG | Códec acotado en 2.0.0 y migración Qt candidata. Portables descartables de Windows y Linux | Mitigado parcialmente en 2.0.0. Versión corregida para este aviso y verificada en los portables candidatos. |
| WP-03 · CPython | Avisos oficiales, consulta NuGet y manifiesto de GitHub Actions | Pendiente en Linux. Bloqueado en el canal NuGet Windows actual. |
| WP-03 · Tamaño de MATLAB | El archivo `.m` se rechaza antes de la lectura si requiere más memoria que la estimada disponible | Corregido y verificado en Windows/Linux. |
| WP-03 · Plazos y escalas | Cancelación cooperativa y terminación del worker auditadas. Límites y exposición documentados | Mitigado parcialmente. Presupuesto común y perfiles de estrés pendientes. |
| WP-04 · Líneas y ramas | `coverage.py` sobre suite completa. Datos de proceso y métricas por motor | Medición verificada en ambos sistemas. Los porcentajes quedan por debajo de los objetivos orientativos. |
| WP-05 · Apertura, migración y guardado | Sesiones creadas con los escritores 1.9.3, 1.9.4 y 2.0.0. Resultados, relaciones y relojes comprobados | Verificado en Windows/Linux para esas rutas históricas. |
| WP-05 · Recuperación y corrupción | Pruebas de escritura interrumpida y rechazo de referencias inválidas | Verificado en Windows/Linux en el perfil offscreen. |
| WP-06 · Grafo y ADR | AST, componentes cíclicos y evaluación de las representaciones. Un flujo piloto definido | Verificado para el grafo. ADR propuesto. |
| Distribución 2.0.0 | Validación nativa de instaladores y manifiestos de la estable | Verificado para el SHA del release. |
| Distribución del candidato | Instalador, actualización, firma y publicación | No aplicable a los portables descartables de auditoría. |
| Fase 02 y laboratorios nuevos | Implementación de la arquitectura objetivo | No aplicable a la autorización de Fase 01. |
