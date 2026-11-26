# Matriz de validación de Fase 03

## Consolidación de 02C

Un único despacho de Mathematical reliability, sobre `a5eafa9a1e98116e84b57d3bb0e8881ea02b2931`. La matriz verifica por separado la suite, el portable descartable y la distribución en Windows x64 y Ubuntu x86-64. El verificador reúne la evidencia de ambos sistemas para el mismo SHA. [Corrida e informes](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45812233593)

## Verificación inicial de comunicaciones

| Evidencia | Entorno y resultado |
| --- | --- |
| Referencias de pulsos | SciPy, 79 valores mediante cuadratura del espectro de RC o RRC. Incluye el límite exacto y puntos vecinos. |
| Etiquetas y energía | Reflexión Gray de 3 y 2 bits y suma de energía de 4, 16, 64 y 256-QAM. |
| BER coherente | Cinco valores de la integral de probabilidad antipodal. |
| Errores en QAM | Veinte combinaciones de orden y Eb/N0 mediante integrales gaussianas sobre regiones de decisión y distancia de Hamming para Gray. |
| Comparador externo | Komm 0.37.0, ejecutado aparte. Detecta discrepancias en puntos vecinos de polos de RRC. |

[Métodos y reproducción](MATHEMATICAL_AUDIT.md) · [Reglas para completar la validación](QUALITY_GATE_CRITERIA.md)
