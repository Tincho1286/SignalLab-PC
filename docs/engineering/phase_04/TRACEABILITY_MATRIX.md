# Trazabilidad de Fase 04

La evidencia de cada implementación se registra en el [log](IMPLEMENTATION_LOG.md). El estado parcial indica que el Quality Gate del requisito abarca funciones o plataformas adicionales.

| ID | Requisito | Implementación y verificación | Estado |
| --- | --- | --- | --- |
| CH-00 | Línea base y contratos | Referencias remotas, candidato histórico, control QPSK/RRC/AWGN, compatibilidad y criterios previos. [Línea base](PHASE_04_BASELINE.md). | Línea base verificada |
| CH-01 | Multitrayecto | `MultipathSpec`, `apply_multipath`, `analyze_multipath`, `multipath_frequency`. Convolución, `freqz`, perfil y momentos manuales, persistencia y cancelación. [Contrato](SCIENTIFIC_CONTRACTS.md) · [Retardo fraccionario](DECISION_LOG.md). | Implementado, pendiente matriz final |
| CH-02 | Rayleigh y Rician | Motores independiente y Clarke. Comparación con distribuciones SciPy, K lineal/dB, fase, potencias y semillas. | Implementado, pendiente matriz final |
| CH-03 | Canal variante y Doppler | `CarrierShift`, cuadratura Clarke, autocorrelación, PSD y coherencia. [Oráculos](MATHEMATICAL_AUDIT.md#protocolo-previo-para-doppler). | Implementado, pendiente matriz final |
| CH-04 | Imperfecciones e interferencia | CFO, fase, llegada, SFO, fase Wiener e I/Q con DC e IRR. Interferencia tonal, en banda cocanal o adyacente, externa y con AWGN opcional. Potencias, SIR, SNR y SINR verificadas con oráculos. | Implementado, pendiente matriz final |
| CH-05 | Pérdidas y composición | Ganancia, espacio libre, log-distancia, sombra y cadena ordenada. Huellas, relojes, subflujos separados, potencias, condiciones y estados intermedios. | Implementado, pendiente matriz final |
| CH-06 | Enlace y sincronización | La cadena se aplica entre TX y RX, con referencia conocida, alineación asistida o estimación por piloto. Control histórico preservado. Se omiten métricas cuando el reloj o el instante resultan incompatibles. | Implementado, pendiente matriz final |
| CH-07 | Workbench, API y CLI | Modelos y laboratorios de cadena, enlace y barridos por servicios compartidos. Densidades observadas y teóricas de fading con selector de trayectoria, API común y archivo verificable desde CLI. Faltan la paridad integral y el escritorio real del candidato. | Parcial |
| CH-08 | Barridos y almacenamiento | Ejes de enlace y canal, réplicas, medias e intervalos, CSV, huellas, archivos de fuentes externas y recuperación. | Implementado, pendiente matriz final |
| CH-09 | Calificación científica y recursos | Oráculos de las operaciones, cobertura invariable, rendimiento y riesgos conforme a los [criterios](QUALITY_GATE_CRITERIA.md). | Parcial |
| CH-10 | Expediente y 2.2.0 Preview | Matriz limpia de dos sistemas, instaladores, portables, hashes, licencias, fuentes y dictámenes. | Pendiente |
