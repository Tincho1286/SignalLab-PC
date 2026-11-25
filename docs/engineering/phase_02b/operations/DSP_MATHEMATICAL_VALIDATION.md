# Validación matemática DSP

| Referencia independiente | Aceptación |
| --- | --- |
| Exponentes complejos de la inversa | Comparar una suma con normalización 1/N y probar también un espectro histórico. |
| Sinc ideal y sumas de retardo | Comparar coeficientes de ventana rectangular y muestras de una convolución directa compleja. |
| Filtro Kaiser y remuestreo | Reconstruir un kernel pequeño mediante sinc y evaluar su convolución en índices de salida, incluidas reglas de longitud y tiempo. |
| PSD y potencia | Usar secuencias constantes, sinusoides y ruido con semilla fija. Comprobar analíticamente los bins, la potencia media y el plegado en longitudes pares e impares. |

Los vectores ejecutables se encuentran en `tests/test_math_dsp_application.py`. La ventana y las condiciones de borde son parte de cada oráculo.
