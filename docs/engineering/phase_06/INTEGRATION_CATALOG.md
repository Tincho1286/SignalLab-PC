# Interfaces RF y referencias

| Capacidad | Frontera que comparte el cálculo |
| --- | --- |
| Redes y cascadas | `rf_network` y `rf_analysis` |
| Líneas, adaptación y Smith | `rf_line` y `rf_matching` |
| Bessel | `analog_design`, `Transfer` y diseñador de filtros analógico |
| Potencia, ruido y dispositivo | `rf_link` y propagación de comunicaciones |
| Zoom FFT, Chirp-Z y ventanas | `advanced_fourier`, `window_signals`, `window_spectrum` y `Signal` |
| Barridos y campañas | `rf_experiments` y campaña Monte Carlo existente |
| Contrato de solicitud y entrega | `RFRequest`, `run_rf`, `store_rf` y `python -m signallab_pc rf` |
| Archivos | `touchstone`, `rf_storage`, `Project`, JSON y SLPROJ |

Las operaciones usan SciPy y NumPy del entorno bloqueado. scikit-rf aporta documentación de convenciones y un comparador posible. ngspice y Qucs-S permiten cotejar circuitos de CA mediante archivos o procesos externos. openEMS queda como referencia arquitectónica electromagnética. [Alcance](AUDIT_AND_SCOPE_REPORT.md) · [Ejemplos](RF_API_EXAMPLES.md)
