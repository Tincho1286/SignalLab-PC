# Registro de implementación de Fase 05

## Línea base y criterios

Se verificaron las ramas, la versión LTS, la Preview y el código equivalente al candidato de Fase 04 antes de modificar motores. Se recuperaron y verificaron los informes de Windows y Ubuntu y se ejecutaron 55 regresiones locales. El inventario identificó generadores, ajuste AR, PSD, covarianza, fading, semillas y almacenamiento reutilizables. [Línea base](PHASE_05_BASELINE.md)

Se registraron los requisitos ST-00 a ST-10, contratos científicos y oráculos antes de implementar. El Quality Gate de Fase 05 va a reutilizar la evaluación de Fase 04 sobre el nuevo SHA. Tendrá informes adicionales de ciencia, recursos y demostradores para que un candidato incompleto no se pueda calificar. [Criterios](QUALITY_GATE_CRITERIA.md) · [Protocolo](STATISTICAL_VALIDATION_PROTOCOL.md)

## Distribuciones y primer recorrido

Se incorporaron 23 familias escalares y las gaussianas conjuntas real y compleja y la multinomial. Se preservó la ruta original de generación, se añadió la consulta desde el mismo panel y se integraron subflujos, componentes, reloj y persistencia transaccional. La cola de Rician se validó con cuadratura independiente. Los ensayos de Workbench comprobaron valores y metadatos contra Python, reapertura y cancelación. [Arquitectura](ARCHITECTURE.md) · [Trazabilidad](TRACEABILITY_MATRIX.md)

La corrida focalizada de Windows aprobó 58 pruebas con Qt offscreen y un hilo BLAS/OMP. La cobertura local registró 246/252 líneas y 108/114 ramas en `probability.py`, 195/208 y 43/50 en `multivariate_probability.py`, y 98/98 y 46/46 en `probability_cli.py`. La autocomprobación en código fuente aprobó el nuevo caso de distribución y SLPROJ. El empaquetado nativo se verificará en el candidato de 2.3.x.

## Infraestructura de candidato

Se agregó el selector `phase_05`, su verificación de fuente, la matriz acumulativa y la evaluación de la evidencia específica. Las pruebas de vigencia del publicador rechazaron un Quality Gate de otra fase y una versión incompatible. El análisis estático de Python y `actionlint` aprobaron. Los reportes de calificación estadística y rendimiento de toda la fase quedan pendientes de implementación. [Guía de publicación](../../development/releases.md#adaptaciones-pendientes-del-flujo)

## Estadística descriptiva

`29094a4` pasó los controles automáticos de desarrollo de GitHub. El siguiente lote amplía la ruta de estadística con análisis por proyección, mediana, moda, momentos, medidas robustas, cuantiles, CDF/CCDF, caja y Q–Q. Para fases a ambos lados de ±π se informa la dirección circular. La fase de las muestras nulas se excluye y el conteo queda en el resultado. [Controles del primer lote](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46005000910)

El cálculo de cuantiles interpola en escala binaria local para preservar observaciones pequeñas frente a registros de gran rango. El promedio conserva la cancelación de términos grandes cuando es representable. Los estados numéricos describen momentos que no caben en el tipo de salida. Se mantuvo la regresión que conserva las medidas si falla el histograma.

Se ejecutaron 30 pruebas focalizadas de probabilidad, estadística, escritorio y verificador en Windows. `descriptive_statistics.py` obtuvo 131/131 líneas y 36/36 ramas y `statistics_cli.py` obtuvo 34/34 líneas y 4/4 ramas en esa corrida. También aprobaron el análisis estático y `actionlint`. El ajuste inferencial y su calificación estadística siguen en WP-02.

## Inferencia y ajuste

El panel de estadísticas conserva su ruta descriptiva y habilita ajustes y contrastes por selección. Python, CLI y Workbench usan el mismo motor. Los informes mantienen las hipótesis, cotas, relojes, componentes, exclusiones y huellas de las entradas. La entrega del informe y de las entradas que aún están en borrador pasa por una transacción del proyecto. Los parámetros ajustados e intervalos se documentan con sus modelos.

La interpolación de Anderson–Darling devuelve un extremo de tabla en colas fuera de su calibración. El informe lo traduce a una cota y permite una decisión indeterminada. Se corrigieron dos problemas de rango en cálculos de medias. Las sumas parciales que desbordan se acumulan como enteros binarios exactos y los contrastes cerca del nulo recuperan la fracción de la media antes de redondear.

En Windows aprobaron 29 pruebas focalizadas con Qt offscreen. Incluyen campaña IID de 256 réplicas, oráculos de pivotes y parámetros, errores de hipótesis, cancelación, rechazo por presupuesto, reapertura y paridad con las rutas de interfaz y consola. La cobertura de líneas y ramas fue 336/344 y 143/148 en `statistical_inference.py`, 128/128 y 36/36 en `descriptive_statistics.py`, 83/83 y 17/18 en `statistics_cli.py` y 15/15 y 4/4 en `statistics_results.py`. El comando fue `python -m coverage run --rcfile=tools/engineering.coveragerc -m unittest test_statistical_inference test_probability_desktop test_descriptive_statistics test_phase05_quality_gate test_workflow_contracts.WorkflowContracts.test_statistics_survive_an_unavailable_histogram -q`. Esta evidencia focalizada precede a la calificación del candidato. [Validación](STATISTICAL_VALIDATION_PROTOCOL.md)

## Transiciones y generación de trayectorias

El commit `9626d03` aprobó los controles de desarrollo en GitHub. El nuevo lote agrega seis procesos al generador existente y al CLI headless. La primera muestra conserva la condición inicial. Las transiciones y los momentos reportan la convención de tiempo, estado y distribución. El generador persiste todos los registros con el modelo y verifica las huellas de procedencia antes de aceptar el lote. [Controles del lote inferencial](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46010017321)

En Ornstein–Uhlenbeck, una tasa de retorno pequeña podía dejar el coeficiente de un paso redondeado a uno y borrar la deriva respecto del equilibrio. Se calcula la trayectoria de la media con la respuesta exacta a la condición inicial y `expm1`, y se superpone la fluctuación gaussiana. Esto conserva el efecto en la trayectoria cuando la media y la tasa tienen escalas muy distintas.

En Windows aprobaron 31 pruebas focalizadas con Qt offscreen y un hilo BLAS/OMP. Los oráculos incluyeron 2048 trayectorias por modelo no degenerado, transiciones, covarianza, relojes, semillas, estados absorbentes, preservación del destino, corrupción previa a la entrega, paridad Workbench/Python/CLI y reapertura de SLPROJ. La cobertura de líneas y ramas fue 295/298 y 99/102 en `stochastic_processes.py`, 41/41 y 2/2 en `stochastic_cli.py` y 17/17 y 6/6 en `realization_batch.py`. El comando fue `python -m coverage run --rcfile=tools/engineering.coveragerc -m unittest test_stochastic_processes test_probability test_probability_desktop test_phase05_quality_gate -q`. [Protocolo](STATISTICAL_VALIDATION_PROTOCOL.md)

## Ruido por ley, FIR y PSD

El commit `80e942f` aprobó los controles de desarrollo. El generador incorpora ruido blanco propio real o complejo, mezcla impulsiva, filtrado FIR con prehistoria y síntesis por color o densidad bilateral. Una grilla sin soporte para la densidad solicitada se rechaza con una explicación. La PSD teórica puede abrirse y reutilizarse. [Controles del lote de procesos](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46011828554)

Windows aprobó 37 pruebas focalizadas con Qt offscreen y un hilo BLAS/OMP. Se compararon la DFT directa, la potencia, las pendientes, la asimetría permitida, la convolución con ruido previo y la calibración en 2048 réplicas. Workbench y CLI reabrieron los mismos resultados de Python. La cobertura fue 223/226 líneas y 87/90 ramas en `stochastic_noise.py`, y 56/57 y 9/10 en `stochastic_cli.py`. El comando fue `python -m coverage run --rcfile=tools/engineering.coveragerc -m unittest test_stochastic_noise test_stochastic_processes test_probability_desktop test_statistical_inference test_phase05_quality_gate -q`. [Protocolo](STATISTICAL_VALIDATION_PROTOCOL.md)

## Correlación, covarianza y conjuntos

El commit `2f11b48` aprobó los controles de desarrollo de GitHub. El núcleo de correlación usa un único convenio y permite suma directa y FFT. El intervalo se limita a los índices observados y se verifican los relojes declarados. Los resultados conservan las huellas de entrada y se entregan en una transacción. Las matrices distinguen covarianza, pseudocovarianza y correlación normalizada. Los momentos de conjunto calculan incrementos y agregan una referencia teórica cuando las realizaciones comparten un modelo de proceso registrado. [Controles del lote de ruido](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46012939159)

Windows aprobó 94 pruebas focalizadas con Qt offscreen y un hilo BLAS/OMP. La cobertura fue 214/216 líneas y 76/78 ramas en `stochastic_covariance.py`, 116/117 y 24/26 en `stochastic_cli.py` y 22/22 y 8/8 en `statistics_results.py`. Se verificaron los casos de reloj y escala históricos junto con las nuevas pruebas de pares complejos, semidefinitud, independencia declarada, modelo de referencia y proyecto reabierto. Comando `python -m coverage run --rcfile=tools/engineering.coveragerc -m unittest test_stochastic_covariance test_stochastic_processes test_stochastic_noise test_probability_desktop test_audit_numeric_clocks test_math_contracts test_statistical_inference test_phase05_quality_gate -q`. [Oráculos](STATISTICAL_VALIDATION_PROTOCOL.md)

## Burg y autocorrelación parcial

El commit `f58feb3` aprobó los controles de desarrollo. WP-04 empieza con Burg en el estimador AR y PACF para el modelo teórico y los residuos. Se conserva el recorrido de Yule–Walker, mínimos cuadrados y comparación de órdenes con muestras comunes. Las varianzas de Burg se calculan con los coeficientes de reflexión y se distinguen del residuo observado. [Controles de correlación y covarianza](https://github.com/Tincho1286/SignalLab-PC/actions/runs/46014785842)

Windows aprobó 72 pruebas focalizadas. Los oráculos incluyen un denominador de segundo orden calculado con sumas escalares, la recuperación de un AR(1) conocido y la PACF por inversión directa de Toeplitz. El comando fue `python -m coverage run --rcfile=tools/engineering.coveragerc -m unittest test_ar_estimation test_sample_coordinates test_math_contracts test_phase05_quality_gate -q`. La cobertura de `time_series_identification.py` fue 56/58 líneas y 22/24 ramas. Las coberturas focalizadas de `ar_estimation.py` y `random_models.py` aún dejan brechas en la calificación de componentes críticos, que permanecen visibles en el Gate. [Protocolo](STATISTICAL_VALIDATION_PROTOCOL.md)
