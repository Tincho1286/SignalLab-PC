# Registro de implementación

## 25 de noviembre de 2026 · Revisión de WP-02C.03 y WP-02C.06 · C03, C06 · C-03, C-07

**Estado inicial.** `caf7bcd`. La comprobación del diseño FIR se aplicaba al modelo publicado. El objeto de especificaciones se contrastaba sólo durante la primera publicación. La línea base intermedia midió brechas en importación binaria y CLI.

**Decisión y evidencia.** Se incorporó la huella de la especificación al registro de proyecto. Se probaron la sustitución de parámetros y la reapertura. También se ejercitaron cancelación entre bloques, cabecera incompleta, rechazo antes de reservar muestras y argumentos de sesión del CLI. Se mantienen la API experimental y el esquema de proyecto.

## 25 de noviembre de 2026 · Revisión de WP-02C.03 · C03 · C-03

**Estado inicial y causa.** Una transferencia aceptada por el motor se podía volver a normalizar al abrirla. Se reprodujo con un FIR de coeficiente a₀ = −90,1 + 33,2j. La huella del registro y la del objeto diferían en el cero con signo.

**Decisión y comprobación.** `filters.py` conserva el uno exacto y `project.py` usa la representación de cálculo en los casos históricos de pivote redondeado. Se agregó una regresión de publicación y reapertura y se ejecutaron 23 casos de procedencia, sistemas y proyectos. Se conserva la normalización previa para entradas con a₀ no unitario.

## 25 de noviembre de 2026 · WP-02C.10 · C10 · C-10

**Estado inicial.** `37ac1d4`. Se inspeccionaron las interfaces, el proyecto, la sesión y el costo de persistencia, con foco en las dependencias importadas del Core.

**Evidencia.** El grafo de AST abarcó 26 módulos transitivos y 11 entradas sin ciclos directos. Una sonda dinámica bloqueó importaciones Qt y publicó un pipeline de seis registros. Se revisaron I/Q, reloj, filtros y reproducibilidad sin implementar laboratorios.

**Estado.** Contratos y preparación documentados. La autorización para ampliar el Core sigue separada.

## 25 de noviembre de 2026 · WP-02C.09 · C09 · C-09

**Estado inicial.** `b036fd9`. La estable y el candidato declaran 2.0.0. El instalador nativo y el verificador de transporte se auditaron junto con la prueba que rechaza una actualización a igual número.

**Evidencia.** La corrida intermedia 45646503672 aprobó los candidatos nativos de ambos sistemas. Los instaladores y SBOM definitivos corresponden al SHA candidato. Se conserva pendiente el salto real desde 2.0.0 con una futura versión y canal autorizados.

**Decisión.** Mantener la numeración y conservar las pruebas con claves y perfiles descartables.

## 25 de noviembre de 2026 · WP-02C.08 · C08 · C-08

**Estado inicial.** `825ecfb`. El capturador heredado abría tres vistas con tamaños y escalas parciales. Se amplió a diez vistas y siete perfiles. Se inspeccionó el escritorio Windows real en modo compacto desde el buscador hasta el gráfico DFT.

**Evidencia.** Se generaron diez capturas por perfil offscreen en Windows para las seis combinaciones iniciales. La matriz definitiva agrega 960 × 540 al 200 %. Un gráfico de DFT muestra la fase de residuos numéricos; se registra como cuestión de legibilidad.

**Estado.** Protocolo reproducible disponible. Falta una validación real adicional de escalas y Linux.

## 25 de noviembre de 2026 · WP-02C.07 · C07 · C-05

**Estado inicial.** `c1bc5b2`, con perfiles previos que medían núcleos y almacenamiento por separado. El banco nuevo cubre 57 perfiles y conserva los efectos de memoria, cache y archivos.

**Evidencia.** La corrida exploratoria Windows fue satisfactoria en todos los tamaños admitidos y los ocho ensayos de cancelación. La matriz medirá los perfiles finales en Windows y Linux, dentro de un checkout limpio.

**Riesgo residual.** Las mediciones no definen cuotas ni tiempos máximos bajo carga coexistente.

## 25 de noviembre de 2026 · WP-02C.06 · C06 · C-07

**Estado inicial.** `924154a`. Se revisó la matriz de oráculos y la cobertura heredada. Se priorizaron admisión, plazos, CLI y el caso IIR de alto condicionamiento.

**Decisión y evidencia.** Se conservaron el descubrimiento y los denominadores. Pasaron 7 pruebas de ejecución/CLI y 10 de sistemas. Pasaron también 31 casos de persistencia, históricos y escritorio del paso anterior. El reporte selecciona los módulos críticos por nombre, sin modificar el conjunto instrumentado.

**Estado.** Cobertura definitiva a partir de los artefactos del candidato.

## 25 de noviembre de 2026 · WP-02C.05 · C05 · C-06

**Estado inicial.** `b5ffa1d`. La cabecera SLBIN aceptaba claves repetidas aunque los documentos JSON de la app ya las rechazaban. Se compararon JSON, arreglos separados, contenedor y HDF5.

**Decisión y evidencia.** Reutilizar el lector JSON estricto y preservar los formatos. Se agregó un oráculo de disposición binaria, orden de bytes y digest. La matriz histórica incluye proyectos, sesiones, diagramas, reloj, ROC, CAS y resultados verificados; la hoja CAS activa conserva su limitación documentada.

## 25 de noviembre de 2026 · WP-02C.04 · C04 · C-05

**Estado inicial.** `8b1c63e`. El CLI honraba la cancelación al terminar la escritura JSON, aunque podía completar el archivo temporal después de que se cancelara. Se inspeccionaron `execution`, `jobs`, `resources`, `atomic_file`, `session` y el banco heredado.

**Decisión y evidencia.** Se preservó `before_commit` y se agregó un checkpoint optativo de codificación. `python -m unittest test_math_core_robustness` pasó 6/6 y comprobó que el destino y el directorio se mantienen. Se agregó un banco aislado para cálculo, pico de memoria y cancelación.

**Estado.** Validación funcional aprobada. Medir la envolvente en WP07 y mantener el alcance cooperativo de las operaciones nativas.

## 25 de noviembre de 2026 · WP-02C.03 · C03 · C-03

La publicación verifica el contenido materializado y los padres antes de la entrega atómica. Pasaron 23 pruebas de cálculo, CLI y transacciones y 5 regresiones específicas de procedencia.

## 25 de noviembre de 2026 · WP-02C.02 · C02 · C-04

Se corrigió el origen de los bins para Fs subnormal y se agregó un oráculo analítico de Nyquist. Pasaron 7 casos locales de adaptadores DSP.

## 25 de noviembre de 2026 · WP-02C.01 · C01 · C-01 y C-02

**Estado inicial.** Auditoría `21b720d`. Se revisaron las rutas MAT, JSON, CSV, importación, imágenes, CAS, sesiones y SLBIN. JSON leía tras un `stat` de ruta. HDF5 recuperaba variables por nombre con resolución implícita. El selector de fondos delegaba la detección a Qt.
**Decisión y cambios.** Conservar formatos y PySide ante la indisponibilidad del parche, seleccionar codecs raster antes de Qt, validar enlaces HDF5 locales y unificar lectura JSON acotada. Se descartó ampliar formatos o sustituir motores de lectura.
**Pruebas y resultados.** OSV para 28 versiones, `test_math_input_integrity.py` 3/3, `test_health_exchange.py` 36/36, PNG y SVG benignos offscreen y `tools/check_static.py` 386 archivos. [Evidencia](security/INPUT_SECURITY_VALIDATION.md).
**Estado final y siguiente paso.** Controles de entrada verificados localmente. SBOM en la próxima matriz. Qt depende de disponibilidad de ruedas y conserva su excepción. Sigue WP02.

## 25 de noviembre de 2026 · WP-02C.00 · C00 · C-01 a C-10

**Estado inicial.** `d29bcb8` limpio. Se inspeccionaron el expediente 00–02B, los registros globales, los contratos de ejecución, persistencia y publicación y las evidencias archivadas. El riesgo de procedencia nace de validar existencia del ID sin cotejar contenido.

**Decisión.** Comparar las referencias remotas, reutilizar la matriz del mismo árbol de implementación y contrastar los hallazgos contra el código. Se evaluó repetir la corrida previa. Reservar las nuevas corridas para un candidato con cambios permite obtener una comparación real.

**Cambios y comprobación.** Se agregaron el registro maestro, la matriz y los criterios de salida. `git diff 8ad3066 HEAD -- signallab_pc tests tools .github` quedó vacío. `git ls-remote` confirmó ramas y tag, `pip check` pasó y la API de Actions confirmó la corrida previa. Los resultados y sus alcances quedaron en la línea base.

**Estado final.** WP00 verificado para la apertura de trabajo. Los hallazgos siguen sujetos a comprobación o corrección. El siguiente paquete revisa dependencias y entradas.
