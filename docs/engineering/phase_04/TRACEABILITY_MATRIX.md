# Trazabilidad de Fase 04

La evidencia de cada implementación se registra en el [log](IMPLEMENTATION_LOG.md). La matriz integral aprobó en Windows y Ubuntu sobre `a3026d2`. El estado parcial identifica comprobaciones pendientes de escritorio real. [Quality Gate](QUALITY_GATE_REPORT.md)

| ID | Requisito | Implementación y verificación | Estado |
| --- | --- | --- | --- |
| CH-00 | Línea base y contratos | Referencias remotas, candidato histórico, control QPSK/RRC/AWGN, compatibilidad y criterios previos. [Línea base](PHASE_04_BASELINE.md). | Línea base verificada |
| CH-01 | Multitrayecto | `MultipathSpec`, `apply_multipath`, `analyze_multipath`, `multipath_frequency`. Convolución, `freqz`, perfil y momentos manuales, persistencia y cancelación. [Contrato](SCIENTIFIC_CONTRACTS.md) · [Retardo fraccionario](DECISION_LOG.md). | Matriz aprobada |
| CH-02 | Rayleigh y Rician | Motores independiente y Clarke. Comparación con distribuciones SciPy, K lineal/dB, fase, potencias y semillas. | Matriz aprobada |
| CH-03 | Canal variante y Doppler | `CarrierShift`, cuadratura Clarke, autocorrelación, PSD y coherencia. [Oráculos](MATHEMATICAL_AUDIT.md#protocolo-previo-para-doppler). | Matriz aprobada |
| CH-04 | Imperfecciones e interferencia | CFO, fase, llegada, SFO, fase Wiener e I/Q con DC e IRR. Interferencia tonal, en banda cocanal o adyacente, externa y con AWGN opcional. Potencias, SIR, SNR y SINR verificadas con oráculos. | Matriz aprobada |
| CH-05 | Pérdidas y composición | Ganancia, espacio libre, log-distancia, sombra y cadena ordenada. Huellas, relojes, subflujos separados, potencias, condiciones y estados intermedios. | Matriz aprobada |
| CH-06 | Enlace y sincronización | La cadena se aplica entre TX y RX, con referencia conocida, alineación asistida o estimación por piloto. Control histórico preservado. Se omiten métricas cuando el reloj o el instante resultan incompatibles. | Matriz aprobada |
| CH-07 | Workbench, API y CLI | Modelos y laboratorios de cadena, enlace y barridos por servicios compartidos. El caso de escritorio Windows y sus reproducciones en Python y CLI coinciden en muestras, reloj, métricas y procedencia. [Contraste](evidence/candidate-2a0a3fd/windows-interface-parity.json). | Matriz y paridad aprobadas. Escritorio real parcial |
| CH-08 | Barridos y almacenamiento | Ejes de enlace y canal, réplicas, medias e intervalos, CSV, huellas, archivos de fuentes externas y recuperación. | Matriz aprobada |
| CH-09 | Calificación científica y recursos | Oráculos de las operaciones, réplicas Clarke, contraste angular con mpmath, rendimiento y riesgos conforme a los [criterios](QUALITY_GATE_CRITERIA.md). | Matriz y perfiles medidos aprobados |
| CH-10 | Expediente y 2.2.0 Preview | Los artefactos corresponden a `a3026d2`. El expediente separa el cierre técnico, Fase 05 y la distribución pública. [Dictámenes y recibos](QUALITY_GATE_REPORT.md) · [Matriz](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45905864702). | Parcial. Pendiente escritorio real |
