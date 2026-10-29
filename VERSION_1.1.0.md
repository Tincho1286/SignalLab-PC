# SignalLab PC 1.1.0 · primera ampliación de Señales Aleatorias

- Nuevo documento Modelos de procesos: analizar modelos AR, MA o ARMA conocidos y estimar un AR desde datos mediante Yule–Walker.
- Media, varianza, potencia, autocovarianza, autocorrelación y densidad de potencia del modelo, separadas de las medidas del registro. Se informa la línea ideal en frecuencia cero cuando la media es no nula.
- Realizaciones gaussianas con estado inicial estacionario y semilla reproducible. Se conservan los relojes conocidos al reutilizar sistemas y registros.
- Estimación AR con orden elegido, coeficientes, varianza de innovación, espectro paramétrico y residuo sobre índices con antecedentes observados.
- Correlación y covarianza auto/cruzada en una sola herramienta, con alineación por índices, divisor explícito y normalización opcional. La conjugación de datos complejos se conserva.
- H(z), curvas, registros y resúmenes quedan en Resultados. Los modelos pueden exportarse y reutilizarse en el análisis de sistemas y CAS. Gráficos discretos con tallos, frecuencia en rad/muestra y figuras independientes.
- Ayudas con explicaciones de cada parámetro e ilustraciones en colores. Se conserva la generación y estadística anteriores.

La navegación reúne ahora 30 problemas y 82 variantes, más CAS. Esta versión inicia la ampliación de Aleatorias; no declara cobertura total. Markov/Poisson, detección, Wiener/Kalman y estadística inferencial siguen pendientes según COBERTURA_SENALES_ALEATORIAS.md. El alcance de Sistemas y Señales I/II se mantiene.

Se realizaron comprobaciones dirigidas de casos analíticos, correlación compleja, ajuste AR, reutilización y presentación. No se ejecutó una batería general.
