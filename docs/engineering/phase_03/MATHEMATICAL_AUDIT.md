# Auditoría matemática inicial

Se generaron referencias independientes antes de programar los motores. Para RC y RRC se integró el espectro ideal directamente, separando la meseta y la transición y usando su simetría par. Así se evalúan puntos incluso cuando la expresión temporal tiene una singularidad removible. Para BPSK se integró la cola gaussiana. Las etiquetas Gray se obtuvieron por reflexión recursiva y la energía de QAM cuadrada por suma explícita de niveles.

```sh
python tools/audit_communications_reference.py --output work/analytical-reference.json
```

Los vectores cubren roll-off 0, 0,2, 0,25, 0,5 y 1 y ambos lados de cada singularidad finita a una distancia de 10⁻⁷ períodos de símbolo. Se incluyen energías de 4, 16, 64 y 256-QAM y BER antipodal en cinco valores de Eb/N0. [Vectores](evidence/analytical-reference-v1.json) · [Convenciones](MATHEMATICAL_FOUNDATIONS.md)

La referencia QAM integra la gaussiana en todas las regiones de decisión de cada eje. Para BER pondera cada transición por la distancia de Hamming entre etiquetas Gray. Los 20 valores de SER coinciden con la fórmula de constelación cuadrada y los cinco de BER de 4-QAM coinciden con la integral antipodal. En 256-QAM a 0 dB, el BER exacto de referencia es 0,254607 y la aproximación por vecinos da 0,177892. Esta diferencia exige que el informe identifique la aproximación y su alcance. [Probabilidades de referencia](evidence/analytical-reference-v1.json)

Como contraste adicional se instaló Komm 0.37.0 únicamente en un directorio de auditoría con tqdm 4.67.3 y el NumPy del entorno fijado. En esa versión el RRC se obtiene con `RaisedCosinePulse(rolloff).root()`. Coincidieron el ciclo Gray de ocho etiquetas, las cuatro energías de QAM y RC en la grilla. RRC coincidió en los puntos ordinarios y en las singularidades con error absoluto de hasta 2,3 × 10⁻¹⁶. En la vecindad inmediata de los polos, la discrepancia de Komm llegó a 2 × 10⁻⁷. Esta comparación justifica usar la cuadratura como oráculo principal en esas vecindades. [Comparación](evidence/komm-comparison-v1.json) · [Modelo de pulsos](https://komm.dev/ref/RaisedCosinePulse/)

Con Komm instalado en un entorno de auditoría se reproduce la comparación mediante `python tools/audit_communications_reference.py --compare-komm --output work/komm-comparison.json`. Los experimentos Monte Carlo y las pruebas de recuperación, EVM y cancelación se incorporan al desarrollar sus contratos y servicios.
