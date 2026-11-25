# Registro de implementación

## 25 de noviembre de 2026 · C-04 y C-07 · Ventanas de Fourier y continuidad de resultados

**Causas.** La vista de Fourier expandía productos en una suma, pero dejaba adiciones anidadas por el analizador de fórmulas. Una rama podía contener varias deltas ordinariamente separadas y llegar como si fuera un producto de distribuciones. El contrato de rejilla convertía la cantidad a entero sin validar y permitía un intervalo cuya diferencia excedía el rango de representación. La reconstrucción por invarianza del sistema nulo entraba en el descomponedor de residuos aun sin polos.

**Cambios.** La extracción separa los sumandos antes de validar cada línea. Se conserva el área y la regla que cuenta una sola vez el extremo de un período. La rejilla exige una cantidad entera y una amplitud de intervalo representable. La inversa del sistema nulo conserva un sistema analógico cero. Se validan explícitamente los métodos de conversión, los sentidos del mapeo, su rama entera y la elección de contorno.

**Rango y entrada MAT.** La normalización de ganancia calcula el módulo mediante mantisa y exponente cuando el complejo es finito pero su módulo desborda. La prueba compara amplitud y fase, además de escalas subnormales y SOS. El catálogo HDF5 admitía códigos de caracteres si `MATLAB_class` llegaba como Unicode. El mismo criterio de clase se aplica ahora en catálogo y lector. Se verificaron dos representaciones de la etiqueta de texto, una matriz compleja con compresión y un eje entero por encima de 2⁵³.

**Pruebas.** `test_math_transform_workflows` cubre reconstrucción de las líneas desde texto y desde un valor simbólico guardado, área, muestras complejas y dominio. `test_math_study_workflows` comprueba sistema nulo, ambos identificadores de bilineal inversa, parámetros inválidos y ROC. `test_math_lti_workflows` añade oráculos para historiales, secciones, circuitos RC y filtros clásicos. Los flujos de Qt prueban CSV real, fuentes de sesión independientes, selección de un diseño FIR, superposición DTFT/DFT, cursores, procedencia y recuperación del foco.

**Estado.** La corrida agrupada de 186 pruebas aprobó en Windows. Una ejecución anterior detectó la necesidad de preservar el identificador histórico `radius` del contorno manual. Se conservó el alias y se verificaron ambos modos. Las ampliaciones de CAS, comparación, imágenes y normalización se ejecutaron también en grupos instrumentados. La fase mantiene pendiente el objetivo de ramas. [Cifras de continuación](testing/FINAL_COVERAGE_REPORT.md#medición-focal-de-la-siguiente-revisión).

## 25 de noviembre de 2026 · C-04 y C-07 · Cobertura científica y de escritorio

**Polos múltiples.** En la conversión inversa por invarianza al impulso, el cálculo numérico de residuos separaba artificialmente algunas raíces repetidas. La restricción a polos simples se comprueba ahora sobre el denominador racional reducido, con aritmética exacta de los coeficientes almacenados. Las pruebas comparan el mapeo exponencial, incluyen multiplicidad triple y distinguen una cancelación exacta que deja un solo polo.

**Avance temporal en control.** La realimentación y el lugar de raíces construían el polinomio de lazo a partir de coeficientes en z⁻¹ sin incorporar el avance del sistema abierto. La realimentación reutiliza la aritmética de interconexión y conserva el reloj. El lugar de raíces incorpora la potencia de z y representa las ramas en infinito cuando cae el grado. Se comparan los resultados con la ecuación característica y con las fórmulas explícitas H y KH/(1 ± KH).

**Pruebas ampliadas.** Se incorporaron oráculos de DFT e IDFT con origen y fase, filtros FIR/IIR y sus bandas, respuesta forzada y cruces de estabilidad, recurrencias con historial, Fourier y Laplace con distribuciones, más contratos de importación, controles del escritorio, gráfico y tabla, CAS, guías contextuales y reapertura de diagramas. Los ensayos Qt se ejecutaron en modo offscreen en Windows.

**Comandos.** `python -B -X utf8 tools/check_static.py` y `coverage run --branch --source=signallab_pc -m unittest` con los módulos nuevos `test_math_*_workflows` y `test_workbench_{results,navigation,transfer}`. Pasaron 97 casos en la primera ejecución agrupada, incluidos los preventivos de cálculo, y se verificaron por separado las tres pruebas complementarias de documentos de transferencia. La proyección de [cobertura](testing/FINAL_COVERAGE_REPORT.md#medición-focal-de-la-siguiente-revisión) usa la cobertura integral de `eb50895` y el conjunto de líneas y ramas ejecutadas por los casos nuevos. La matriz de ambos sistemas se reserva hasta medir los objetivos globales en el candidato local.

## 25 de noviembre de 2026 · C-02, C-03, C-05 y C-11 · Importación y supervisión de CI

**Entrada y procedencia.** El selector volvía a abrir el JSON después de inspeccionarlo, convertía a listas todas las muestras del proyecto y volvía a publicar cada objeto elegido. Los identificadores del contenido calculado quedaban apuntando a la biblioteca de origen. `7f1babd` reutiliza el documento validado, incorpora el subgrafo necesario con un único cambio de proyecto y vuelve a enlazar tanto padres como referencias calculadas. La copia conserva el origen, reloj y datos compactos. Lecturas de texto, análisis de JSON y preparación de manifiestos SLPROJ participan del mismo pool estimado que el Core.

**Validación focal.** Pasaron 38 pruebas de importación, sesión, proyecto, integridad y procedencia con CPython 3.14.10. El selector real importa una expresión con referencia de resultado, vuelve a cargar la señal compleja y verifica que una importación cancelada no cambia el proyecto. La contención del pool rechaza una lectura antes de decodificar y permite reintentar tras liberar la reserva o corregir un JSON inválido.

**CI.** En `3a68618` Windows cayó por el mismo plazo de 420 s que Linux en `0fc6d5a`. En `99f7ce2` se repitió en ambos sistemas. El ensayo local con el nuevo presupuesto fijo de 540 s también seguía avanzando al terminar. `eb50895` separa 120 s sin progreso de un límite global de 960 s y registra la última prueba iniciada. La suite y sus criterios se conservan y el supervisor local comprobó finalización y terminación de un proceso detenido. Las corridas previas conservan sus resultados y la matriz actual usa un único SHA. [Matriz](validation/FINAL_VALIDATION_MATRIX.md#continuación-autónoma)

## 25 de noviembre de 2026 · C-03, C-05, C-06 y C-07 · Fallos de cálculo y cancelación medida

**Causa y decisión.** Normalización, ajuste de fase, conversiones con transferencia, Z por contorno e interconexión registraban la definición del sistema antes de que se completara el cálculo. Un fallo matemático, una cancelación o una tarea ya en curso dejaban esos registros locales en la biblioteca. Las definiciones y sus vínculos se capturan al pulsar Calcular. El callback de éxito publica entonces la entrada usada y conserva sus relaciones con los resultados. Se reutilizó el contrato de entrega del escritorio.

**Verificación.** La normalización sobre un cero y la realimentación unitaria positiva rechazan el cálculo y dejan el proyecto vacío. El caso de interconexión también cancela con el motor ya iniciado y reintenta hasta obtener H = 1/2. Se verificaron bilineal, fase, reloj y ganancia. Dos casos adicionales de recuperación prueban que un respaldo ajeno sólo se descarta por confirmación expresa y que una denegación de permisos al limpiar libera el lock y conserva los datos.

**Rendimiento.** El banco incorpora cancelación de lectura JSON, SLBIN, SLPROJ y MAT clásico/HDF5. Compara hashes de los archivos antes y después y distingue un cálculo que termina antes del acuse. En Windows local JSON y SLPROJ confirmaron la cancelación, y MAT clásico y HDF5 devolvieron el control con archivos intactos. El perfil rápido de SLBIN terminó antes del acuse. La matriz exige los 22 intentos por sistema y el ensayo del trabajador simbólico. `99f7ce2`.

**Distribución.** En `0fc6d5a`, el verificador nocturno de Linux interrumpió la suite Qt a los 420,115 s. La salida registró las pruebas que seguían ejecutándose y el informe declaró `timed_out`. `4f0f32d` ajusta el presupuesto a 540 s con terminación del árbol de procesos y mensaje explícito. Se conservan el conjunto de pruebas, la instrumentación y los criterios de aprobación. [Matriz](validation/FINAL_VALIDATION_MATRIX.md) · [Trabajo fallido de CI](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45684469040/job/139453298590)

## 25 de noviembre de 2026 · C-06 y C-11 · Recuperación cuando cambia la sesión

**Causas.** En Windows nativo, resolver el widget activo por método de instancia fallaba si una hoja CAS guardaba una referencia a la ventana con el mismo nombre. Además, al cambiar de documento mientras el escritor terminaba, un checkpoint de la sesión anterior podía quedar como oferta de recuperación incluso después de descartar esa sesión. La lectura JSON tenía un único bloque sin comprobaciones intermedias.

**Cambios.** `0fc6d5a` resuelve el widget activo por el método de Qt y prepara la hoja CAS antes de cambiar de sesión. El escritor identifica el documento por generación. Si el usuario confirma el cambio, se retira exclusivamente el checkpoint propio y obsoleto después de que termine el escritor. Rechazar el cambio o encontrar un checkpoint de origen ajeno conserva el archivo. Los archivos JSON grandes se leen en bloques de 1 MiB y verifican la cancelación antes y después de analizar JSON. El análisis nativo continúa teniendo límites cooperativos.

**Pruebas.** Se confirmó en Windows real la reapertura con foco en la hoja, resultado complejo preservado y borrador pendiente. La regresión automatizada compara los mismos valores. También se verificaron cambio de sesión con escritura ya publicada y notificación pendiente, fallo de permisos y reintento, rechazo de sustitución, reapertura de un JSON histórico y contrato CAS sin importar Qt o el motor CAS. Las integraciones de escritorio agregan oráculos de fase, ganancia, cuantización exacta, tablas y compensación FIR. [Acta de escritorio](gui/DESKTOP_CONTINUATION.md)

## 25 de noviembre de 2026 · C-05, C-06 y C-11 · Continuidad autónoma

**Causas.** La admisión por solicitud dejaba el pool como opción. La recuperación automática serializaba JSON en el hilo de Qt. Las hojas CAS sólo conservaban resultados publicados. El cierre anterior agregaba evidencia de CI manualmente.

**Cambios.** Se usa la reserva estimada del proceso en ExecutionContext y en la lectura y escritura de SLPROJ. El escritorio captura widgets en su hilo y envía una instantánea de datos a un escritor exclusivo. Se conservan los puntos JSON de recuperación históricos. La sesión guarda CAS con un contrato versionado, verifica las referencias de las celdas y vuelve a mostrar los resultados almacenados. Se agregó un banco de campaña y un agregador de evidencia por SHA para CI.

**Validación local.** 40 pruebas focales aprobadas con CPython 3.14.10. El guardado con I/O detenido por el ensayo permitió ejecutar un temporizador de Qt y retuvo el estado anterior hasta completar la escritura. SLPROJ obtuvo 93,91 % de líneas y 86,00 % de ramas. El contrato CAS alcanzó 100 % de líneas y ramas en la muestra focal. El banco sintético local verificó 48 corridas, 288 registros y 75 497 472 muestras. Usó 1 208 085 276 bytes de disco y tuvo 150,8 MiB de RSS pico, con cálculo, guardado, reapertura y verificación en 22,7 s. Es un resultado exploratorio de Windows, previo a la matriz.

**Comandos.** `python -m coverage run -m unittest test_math_project_archive test_math_cas_session test_math_dft_pilot test_math_dsp_pipeline test_desktop_session`, `coverage combine`, `coverage json`, `python tools/measure_scientific_campaign.py --output work/02c-autonomous-local/campaign-48.json` y `python tools/check_quality_gate_02c.py --input work/phase02c-ci-45673548563 --candidate faef335bb7892cda92edc50a7c4f417a89b0415c --output work/02c-autonomous-local/historical-gate`.

**Pendientes de verificación.** Matriz limpia en Windows y Linux para el candidato nuevo, cobertura global, perfiles de recuperación en escritorio y condiciones externas ya registradas. [Registro maestro](audit/MASTER_TECHNICAL_DEBT_REGISTER.md)

## 25 de noviembre de 2026 · Validación de la continuidad 02C

**Candidatos.** `8884ca5485f3a70b9a6d53dcf527741eac12c904` introdujo el lector MAT con cuota, `.slproj`, los oráculos de Core y la verificación del salto estable. `faef335bb7892cda92edc50a7c4f417a89b0415c` corrigió el ajuste inicial Welch, la acción compacta y el control de apertura de proyectos, y amplió el banco. El ensayo de tasas pasabanda comprobó de forma independiente el intervalo abierto 5 < Ωs < 8 para m = 2, el traspaso de Fs a muestreo y el CSV.

**Comandos de referencia.** En CPython 3.14.10 con dependencias fijadas se ejecutaron `python -B -X utf8 tools/check_engineering_baseline.py --output work/engineering-baseline`, `python -B -X utf8 tools/check_engineering_package.py --output work/engineering-baseline/packaged-smoke.json` y `python -B tools/measure_core_hardening.py --output work/distribution-audit/core-performance.json`. Los trabajos de empaquetado ejecutaron `tools/native_sbom.py`, `tools/build_installers.py` y `tools/check_candidate_update.py --from-stable` con los nombres y rutas de cada plataforma.

**Resultados.** Cuatro trabajos aprobados de la corrida 45673548563. 890 pruebas integrales y 150 casos preventivos por plataforma. Las ocho brechas de componentes designados alcanzaron el objetivo. La cobertura global y los controles externos conservan el cierre abierto. Se verificó en Windows real el flujo PSD, informe, figura y sesión compacta. [Quality Gate](validation/QUALITY_GATE_REPORT.md#continuidad-de-fase-02c--25112026) · [Matriz y evidencias](validation/FINAL_VALIDATION_MATRIX.md#matriz-de-la-continuidad)

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
