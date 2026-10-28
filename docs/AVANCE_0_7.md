# Avance 0.7 — operaciones continuas y cambio racional de tasa

## Capacidades añadidas

- Convolución continua numérica: cada registro representa interpolación lineal entre puntos, cero fuera del intervalo. La integral de cada producto de segmentos se calcula exactamente en la rejilla de salida, salvo error flotante. La salida muestreada no afirma exactitud entre sus puntos ni para la función original desconocida.
- Correlación continua cruzada, autocorrelación y normalización por energía, con conjugación compleja y eje de retardos.
- Convolución algebraica: soporte causal explícito o bilateral definido por las expresiones; el motor informa si deja la integral sin resolver.
- Cambio de tasa L/M con FIR polifásico, Kaiser configurable, extensión nula o lineal, reloj físico y retardo compensado para procesamiento offline.
- Todas las nuevas salidas se incorporan al proyecto; las numéricas pueden reutilizarse en otras herramientas.

## Evidencia y límites

56 pruebas de regresión aprobadas el 22/10/2026, salida en work/regression-0.7.txt. Nuevos casos: integración independiente de productos complejos, triángulo por convolución de pulsos, energía y simetría de autocorrelación, gaussianas bilaterales, suma FIR explícita, supresión de aliasing, reloj físico y recorrido Qt convolución → proyecto → CTFT. No es una auditoría de todos los menús HP.

La convolución/correlación numérica exige el mismo paso temporal y al menos dos muestras por entrada. El filtro antialias tiene transición finita y no recupera información ya perdida. Los cálculos de bibliotecas nativas se cancelan al alcanzar puntos de control; no se promete interrupción instantánea dentro de una llamada FIR.

Referencia técnica del remuestreo: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample_poly.html (consultada 22/10/2026). El diseño FIR se hace explícito para registrar longitud y ventana utilizadas.

El objetivo completo permanece activo: falta cerrar toda la matriz HP, ampliar los modelos de sistemas y expresiones, mejorar la persistencia y auditar los flujos restantes. Versiones previas preservadas.
