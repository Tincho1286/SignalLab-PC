# Matriz de validación de Fase 03

## Consolidación de 02C

Un único despacho de Mathematical reliability, sobre `a5eafa9a1e98116e84b57d3bb0e8881ea02b2931`. La suite completa, los portables descartables, la auditoría de instaladores y la consolidación de CI aprobaron. Los recibos conservan las huellas SHA-256 de los informes, incluidos los inventarios y las pruebas de actualización. El informe de CI coincide con la verificación local. [Corrida e informes](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45812233593) · [Recibos](evidence/baseline-a5eafa9-receipt.json) · [Resultados](PHASE_03_BASELINE.md)

## Verificación inicial de comunicaciones

| Evidencia | Entorno y resultado |
| --- | --- |
| Referencias de pulsos | SciPy, 79 valores mediante cuadratura del espectro de RC o RRC. Incluye el límite exacto y puntos vecinos. |
| Etiquetas y energía | Reflexión Gray de 3 y 2 bits y suma de energía de 4, 16, 64 y 256-QAM. |
| BER coherente | Cinco valores de la integral de probabilidad antipodal. |
| Errores en QAM | Veinte combinaciones de orden y Eb/N0 mediante integrales gaussianas sobre regiones de decisión y distancia de Hamming para Gray. |
| Comparador externo | Komm 0.37.0, ejecutado aparte. Detecta discrepancias en puntos vecinos de polos de RRC. |

[Métodos y reproducción](MATHEMATICAL_AUDIT.md) · [Reglas para completar la validación](QUALITY_GATE_CRITERIA.md)
