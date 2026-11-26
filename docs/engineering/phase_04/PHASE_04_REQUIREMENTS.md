# Requisitos de Fase 04

La [matriz de trazabilidad](TRACEABILITY_MATRIX.md) contiene los identificadores CH-00 a CH-10, el estado y la evidencia por bloque. Estos requisitos transversales complementan sus capacidades específicas.

| Requisito | Evidencia de aceptación |
| --- | --- |
| Convenciones explícitas | Cada operación documenta sus unidades, referencia temporal, modelo de potencia, condiciones de validez e identificador de contrato. |
| Persistencia verificable | Las sesiones y campañas de Fase 03 siguen abriendo. Los modelos y señales nuevos completan ida y vuelta y detectan configuraciones o huellas alteradas. |
| Reutilización de motores | Un oráculo reproduce el mismo resultado desde escritorio, API y CLI. El cálculo científico funciona con importación de Qt bloqueada. |
| Enlace válido | El canal deshabilitado reproduce el control QPSK/RRC/AWGN. Los modelos se pueden comparar con métricas condicionadas a alineación válida. |
| Ejecución recuperable | Estimaciones y límites documentados. La cancelación no publica resultados parciales. Campañas interrumpidas retoman corridas verificadas. |
| Calificación | Auditoría matemática y estadística independiente, cobertura y recursos sobre un SHA limpio Windows/Linux, más escritorio real y artefactos de distribución verificados. |
| Separación LTS/Preview | El candidato conserva procedencia de un solo SHA y se valida con manifiestos de prueba. Ramas, etiquetas históricas y la distribución LTS cumplen la política de entregas. |

La evaluación de retardos fraccionarios exige documentar la aproximación antes de habilitarla. SFO se incorpora con un modelo y oráculo reproducibles. Los objetivos de fases posteriores se mantienen fuera de la implementación de este laboratorio. [Decisiones](DECISION_LOG.md) · [Quality Gate](QUALITY_GATE_CRITERIA.md)
