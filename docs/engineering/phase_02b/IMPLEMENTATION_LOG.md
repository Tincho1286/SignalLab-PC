# Registro de implementación

## 25 de noviembre de 2026 · WP-02B.05

Tras `faa190b` se inspeccionaron execution, jobs, reservas existentes, el flujo y el reemplazo atómico. Se eligió un pool optativo con admisión inmediata. La estimación del flujo suma entrada, resultados retenidos y pico temporal. Se probaron dos hilos, liberación tras fallo, plazos anidados, cancelación dentro de Welch, rechazo de presupuesto y reemplazo fallido. Pasaron cinco casos nuevos y tres del flujo. La corrida de almacenamiento terminó con 48 casos exactos por plataforma, por lo que CORE-04 quedó verificado. Permanece una política cooperativa, sin cuota impuesta por el sistema. Commit `phase02b(wp05): enforce cooperative resource admission`. Sigue consolidar API y ejemplos.

## 25 de noviembre de 2026 · WP-02B.04

Desde `9c1366b` se contrastó JSON, NPY, NPZ, HDF5, SigMF y un híbrido. Se agregó el script y se registraron las 48 medidas locales de Windows antes de seleccionar el híbrido. El primer workflow fue rechazado por un valor YAML con dos puntos en un comando de pip. Se corrigió en `6997142`. Tres controles del lector experimental y la regresión de escritura de sesión pasaron en Windows. La verificación de mediciones en runners de ambos sistemas quedó en curso en la corrida `45636393425`. El backend es opcional y los 10 millones de muestras exceden el tope de ensayo. Commit `phase02b(wp04): add optional scientific signal storage`. Continúa la política de recursos mientras finaliza esa verificación externa.

## 25 de noviembre de 2026 · WP-02B.03

Se revisaron los servicios y la frontera de Project en `c77efab`. Se eligió una secuencia tipada en lugar de un grafo. Se añadieron `dsp_pipeline.py`, la CLI compartida y referencias de GUI a las herramientas existentes. Tres pruebas en Windows confirmaron oráculo de flujo, publicación, CLI sin Qt, incompatibilidades y cancelación. El tamaño retenido del flujo se tratará en WP-02B.05. Commit `phase02b(wp03): implement sequential DSP pipeline`. Sigue el benchmark de almacenamiento.

## 25 de noviembre de 2026 · WP-02B.02

Tras `c9cca2c` se revisaron `operations.py`, `filters.py`, `sampling.py`, `fourier.py`, `system_clock.py` y los paneles asociados. Se descartó duplicar los motores y se añadieron solicitudes tipadas y guardas en `dsp_application.py`. Qt usa los adaptadores en IDFT, FIR, cambio de tasa y PSD. Se incorporaron oráculos de suma directa, sinc, kernel Kaiser, tonos y ruido reproducible. Pasaron seis pruebas DSP, doce de reconstrucción y la guarda estática de 380 archivos en Windows. La CLI por operación y los flujos se registran en paquetes posteriores. El commit es `phase02b(wp02): integrate typed DSP operations`.

## 25 de noviembre de 2026 · WP-02B.01

Se inspeccionaron la DFT, jobs, resources y la publicación atómica tras `cb23d43`. El ADR contrasta contextos repetidos y un registro dinámico. Se incorporaron `execution.py`, `operation_provenance.py` y la observación local al hilo con restauración. Se conservaron las firmas DFT y la metadata histórica. `unittest discover -s tests -p test_math_execution_context.py` y la familia DFT pasaron 2 y 6 pruebas en Windows. La interrupción del bloque nativo sigue siendo cooperativa. Este registro acompaña `phase02b(wp01): define execution contracts`. Sigue la integración científica.

## 25 de noviembre de 2026 · WP-02B.00

Partimos de `ff3e762` limpio. Se inspeccionaron `dft_application.py`, `jobs.py`, `resources.py`, `project.py`, `session.py`, los modelos y los accesos de Qt. Se contrastaron `git diff ce6846b ff3e762`, las referencias remotas, la matriz anterior, `pip check` y la familia DFT local. Se evaluó repetir toda la matriz antes de cambiar código. Se reutilizó la corrida exitosa del mismo árbol de código y se repitió la familia local. Se agregaron los cuatro documentos de partida y se actualizaron la hoja de ruta y el backlog. Seis pruebas locales pasaron y se comprobó el bloqueo de la actualización a Qt 6.12.1 por disponibilidad de ruedas. El estado verificable y los riesgos remanentes están en la [línea base](PHASE_02B_BASELINE.md). Este registro acompaña el commit `phase02b(wp00): establish verified baseline`. El siguiente paquete evalúa los contratos compartidos.
