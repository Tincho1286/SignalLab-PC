# Versión 0.39

- Corregida la superposición en DTFT y comparación con DFT: antes recalculaba la curva únicamente en frecuencias de DFT e ignoraba el intervalo y puntos elegidos.
- Ahora usa la misma función DTFT y los mismos parámetros que el cálculo individual.
- La DFT mantiene frecuencias propias y se muestra con tallos, en módulo/fase principal o real/imaginaria. En análisis ampliado se superponen módulo y dB.
- Retirado el texto «bins exactos»; ayuda e informe explican la superposición directa.
- Se respeta el origen de la señal y el intervalo de visualización, incluyendo frecuencias negativas.

Pendiente de empaquetar. No se ejecutaron pruebas funcionales.
