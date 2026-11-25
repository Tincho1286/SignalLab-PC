# Estabilidad numérica

Con Fs = 10⁻³⁰⁹ Hz, el período 1/Fs excede binary64. Para N=4 el eje sí es representable y debe empezar en −Fs/2. El motor obtiene el origen a partir de la razón exacta de índices y verifica que el paso redondeado sea distinto de cero antes de calcular. La prueba permite dos unidades del último lugar en el eje subnormal y usa error relativo 2×10⁻¹⁴ en potencia, cuyo valor de referencia es 4a²/Fs.

El registro de oráculos incluye cancelación, escalas, singularidades e invalidación de resultados fuera de rango. La verificación local de siete casos de adaptadores DSP terminó correctamente. Los resultados de distribución pertenecen al candidato de la fase.
