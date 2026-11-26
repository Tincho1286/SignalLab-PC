# Trazabilidad de Fase 04

La evidencia de cada implementación se registra en el [log](IMPLEMENTATION_LOG.md). El estado parcial indica que el Quality Gate del requisito abarca funciones o plataformas adicionales.

| ID | Requisito | Implementación y verificación | Estado |
| --- | --- | --- | --- |
| CH-00 | Línea base y contratos | Referencias remotas, candidato histórico, control QPSK/RRC/AWGN, compatibilidad y criterios previos. [Línea base](PHASE_04_BASELINE.md). | Línea base verificada |
| CH-01 | Multitrayecto | `MultipathSpec`, `apply_multipath`, `analyze_multipath`, `multipath_frequency`. Convolución, `freqz`, perfil y momentos manuales, persistencia y cancelación. [Contrato](SCIENTIFIC_CONTRACTS.md) · [Retardo fraccionario](DECISION_LOG.md). | Implementado, pendiente matriz final |
| CH-02 | Rayleigh y Rician | Motor independiente por muestra, potencias y distribuciones SciPy, K lineal/dB, fase y semillas. Queda calibrar el proceso temporalmente correlacionado. | Parcial |
| CH-03 | Canal variante y Doppler | Doppler determinista, fading correlacionado, PSD, autocorrelación y tiempo de coherencia. | Pendiente |
| CH-04 | Imperfecciones e interferencia | CFO, fase, llegada, SFO validado, fase aleatoria, tonos, banda limitada, señal externa, cocanal/adyacente e I/Q. | Pendiente |
| CH-05 | Pérdidas y composición | Atenuación, espacio libre, log-distance y sombra. Orden explícito con estado intermedio y procedencia. | Pendiente |
| CH-06 | Enlace y sincronización | Integrar nuevos canales, conservar el control histórico e invalidar métricas si no hay alineación. | Pendiente |
| CH-07 | Workbench, API y CLI | Multitrayecto y fading independiente del mismo servicio, informe, figuras y realizaciones reutilizables. Faltan paridad del resto de modelos y escritorio real en el candidato. | Parcial |
| CH-08 | Barridos y almacenamiento | Cadena, ejes y réplicas, CSV, huellas, recuperación, límites y formatos históricos. | Pendiente |
| CH-09 | Calificación científica y recursos | Oráculos de las operaciones, cobertura invariable, rendimiento y riesgos conforme a los [criterios](QUALITY_GATE_CRITERIA.md). | Parcial |
| CH-10 | Expediente y 2.2.0 Preview | Matriz limpia de dos sistemas, instaladores, portables, hashes, licencias, fuentes y dictámenes. | Pendiente |
