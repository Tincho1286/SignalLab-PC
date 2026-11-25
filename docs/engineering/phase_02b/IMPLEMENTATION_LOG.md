# Registro de implementación

## 25 de noviembre de 2026 · WP-02B.02

Tras `c9cca2c` se revisaron `operations.py`, `filters.py`, `sampling.py`, `fourier.py`, `system_clock.py` y los paneles asociados. Se descartó duplicar los motores y se añadieron solicitudes tipadas y guardas en `dsp_application.py`. Qt usa los adaptadores en IDFT, FIR, cambio de tasa y PSD. Se incorporaron oráculos de suma directa, sinc, kernel Kaiser, tonos y ruido reproducible. Pasaron seis pruebas DSP, doce de reconstrucción y la guarda estática de 380 archivos en Windows. La CLI por operación y los flujos se registran en paquetes posteriores. El commit es `phase02b(wp02): integrate typed DSP operations`.

## 25 de noviembre de 2026 · WP-02B.01

Se inspeccionaron la DFT, jobs, resources y la publicación atómica tras `cb23d43`. El ADR contrasta contextos repetidos y un registro dinámico. Se incorporaron `execution.py`, `operation_provenance.py` y la observación local al hilo con restauración. Se conservaron las firmas DFT y la metadata histórica. `unittest discover -s tests -p test_math_execution_context.py` y la familia DFT pasaron 2 y 6 pruebas en Windows. La interrupción del bloque nativo sigue siendo cooperativa. Este registro acompaña `phase02b(wp01): define execution contracts`. Sigue la integración científica.

## 25 de noviembre de 2026 · WP-02B.00

Partimos de `ff3e762` limpio. Se inspeccionaron `dft_application.py`, `jobs.py`, `resources.py`, `project.py`, `session.py`, los modelos y los accesos de Qt. Se contrastaron `git diff ce6846b ff3e762`, las referencias remotas, la matriz anterior, `pip check` y la familia DFT local. Se evaluó repetir toda la matriz antes de cambiar código. Se reutilizó la corrida exitosa del mismo árbol de código y se repitió la familia local. Se agregaron los cuatro documentos de partida y se actualizaron la hoja de ruta y el backlog. Seis pruebas locales pasaron y se comprobó el bloqueo de la actualización a Qt 6.12.1 por disponibilidad de ruedas. El estado verificable y los riesgos remanentes están en la [línea base](PHASE_02B_BASELINE.md). Este registro acompaña el commit `phase02b(wp00): establish verified baseline`. El siguiente paquete evalúa los contratos compartidos.
