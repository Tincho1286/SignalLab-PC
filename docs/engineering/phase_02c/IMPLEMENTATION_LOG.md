# Registro de implementación

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
