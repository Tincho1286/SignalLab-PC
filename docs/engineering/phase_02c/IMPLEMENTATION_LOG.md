# Registro de implementación

## 25 de noviembre de 2026 · Continuidad 02C · E-03, E-01/02, E-06

**Punto de partida.** `268baa3` documenta `459b9fc`. El análisis de ramas de `coverage.json` identificó límites de precisión, incompatibilidades de dominio, roles de procedencia, errores de selección y cancelación. Se añadieron oráculos por suma directa, energía integrada y evolución de señales, además de regresiones de integración.

**Recursos y MATLAB.** El estimador Linux sólo miraba memoria física del anfitrión y el lector MAT usaba bibliotecas nativas dentro del escritorio. La admisión consulta ahora el menor margen de la jerarquía cgroup v2. La importación clásica y HDF5 se realiza en un proceso limitado por el SO, con identidad del archivo ligada a su descriptor, formatos locales, filtros permitidos, cancelación y plazo.

**Persistencia.** Project duplicaba muestras como listas de objetos Python antes de guardar. Se incorporaron instantáneas NumPy y el contenedor opcional `.slproj`, con muestras binarias y manifiesto versionado en una sustitución atómica. Se conservan la API y el formato JSON. Pasaron 37 pruebas de proyectos, sesiones y flujo, y 17 de matemáticas, entrada e interoperabilidad MAT en Windows.

**Distribución.** `develop` utiliza 2.0.1 como versión de candidato de auditoría. Se comprobó la firma pública del manifiesto histórico 2.0.0. La matriz verifica por separado el salto nativo con clave de ensayo y perfiles descartables. La publicación permanece fuera de este trabajo.

## 25 de noviembre de 2026 · WP-02C.11 · C11 · C-01 a C-10

**Estado inicial.** Desde `d29bcb8`, referencia 02B `8ad3066`. Se descartó una corrida local con fuentes cambiantes y se cotejaron los SHA de los cuatro trabajos de la corrida definitiva 45650373957.

**Evidencia.** El candidato limpio `459b9fc` aprobó 870 pruebas integrales y 150 preventivas por sistema. Se archivaron métricas, SBOM, instaladores, perfiles, mediciones y capturas representativas. Se verificaron los objetivos por módulo y las condiciones que el runner no puede acreditar.

**Dictámenes.** Cierre NO-GO hasta revisar excepciones. Fase 03 GO condicionado de arquitectura. Distribución pública NO-GO. [Puerta de calidad](validation/QUALITY_GATE_REPORT.md) · [Revisión de excepciones](validation/EXCEPTION_APPROVAL_REGISTER.md).

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

**Estado inicial y causa.** `ef15207`. `Project.add` comprobaba la existencia de IDs. `store_pipeline` y `store_dft` podían ligar contenido distinto. Se revisaron `project`, `session`, `execution`, adaptadores, modelos y usos del CLI y Qt.

**Alternativas y decisión.** Una versión de registro sólo serviría dentro de un proyecto. Comparar las listas serializadas exigiría duplicarlas. Se eligieron huellas por bloques, parámetros congelados y verificación contra el estado preparado para commit. Se ajustaron pruebas de cambios de muestras y metadatos, parámetros, padres, reapertura y merge.

**Resultado y límite.** Pasaron 23 casos de cálculo, CLI y transacciones y 5 regresiones iniciales de procedencia. Se conserva el contrato de buffers estables durante la ejecución. La implementación inicial está en `8b1c63e`. Las ampliaciones de normalización y especificación están registradas arriba.

## 25 de noviembre de 2026 · WP-02C.02 · C02 · C-04

**Estado inicial y causa.** `609c8c3`. Se inspeccionaron convenciones de Fourier, muestreo, filtros y estado y pruebas simbólicas por familia. En `fourier.spectral_density`, invertir Fs para obtener el índice de origen podía desbordar aun con un eje representable.

**Alternativas y decisión.** Aumentar precisión del recíproco añadiría una dependencia de plataforma. Construir el eje desde N y Fs da el origen correcto. Se registraron oráculos independientes y se incorporó la regresión de Nyquist, con el rechazo de paso no representable.

**Resultado y límite.** Se ejecutaron siete casos de `test_math_dsp_application`. Se documentaron tolerancias, números subnormales y alcance del gate. Implementación `ef15207`. La suite del candidato acredita el resto de familias.

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
