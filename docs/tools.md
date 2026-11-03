# Herramientas

[← Documentación](README.md)

La navegación agrupa las operaciones por el problema que resuelven. Las variantes compatibles comparten un documento y cada definición mantiene sus propios datos.

## Señales

Creación por fórmulas, tramos y muestras; generación de ventanas simétricas; edición de registros; desplazamiento, inversión y amplitud; componentes par/impar; suma y producto punto a punto; medidas de energía, potencia y RMS.

La multiplicación permite aplicar ventanas a una señal. Las entradas se alinean por sus índices o coordenadas; el origen no se descarta al importar o reutilizar un registro.

## Sistemas LTI

Análisis de H(s) y H(z) por fórmula o coeficientes: módulo lineal/dB, fase, retardo, raíces y realizaciones. Respuesta temporal, condiciones iniciales, conexión en serie/paralelo/realimentación y espacio de estados.

La preliminar 1.2 añade el mapa complejo de H(z), separado de H(e^{jω}), con una ROC explícita. La ubicación de polos bajo una hipótesis causal y la estabilidad de una transferencia bilateral se interpretan con sus condiciones correspondientes.

## Filtros

Diseño FIR/IIR por bandas y tolerancias, FIR por cortes y longitud o h[n] propia, diseño interactivo por polos y ceros, secciones de segundo orden y modelos RC. Ajustes de ganancia y fase; filtros ideales definidos por tramos; conversión analógica/digital por los métodos disponibles.

Las acciones del resultado permiten analizar, exportar y reutilizar el filtro. La preliminar 1.2 incorpora amplitudes por banda y tolerancias absolutas, relativas o en dB; las dos amplitudes independientes de un rechazabanda se diseñan mediante FIR.

## Fourier y espectros

DFT/FFT, DTFT y Fourier continua, con directas e inversas numéricas o algebraicas donde están disponibles. Series, síntesis, densidad de energía, potencia periódica, periodograma/Welch, Hilbert, señal analítica y STFT.

La DFT se representa por sus coeficientes discretos. La DTFT es una curva continua de frecuencia y puede superponerse con las muestras de la DFT sobre ejes compatibles.

## Muestreo y A/D

Muestreo de expresiones, aliasing, tasas pasabanda, reconstrucción, cambios elementales y conversión racional de tasa con antialias. Cuantización, SNR, formatos numéricos y estudio de aritmética de filtros.

Las operaciones elementales de diezmado y expansión no agregan automáticamente un filtro. La conversión racional dispone de su tratamiento antialias explícito.

## Laplace y Z

Transformadas directas e inversas con sus condiciones y regiones de convergencia. Las ecuaciones lineales reúnen ecuaciones diferenciales y en diferencias con coeficientes constantes y condiciones iniciales.

La preliminar 1.2 integra los registros finitos en Z directa; la inversa permite pedir un intervalo o recuperar el soporte completo de un polinomio de Laurent.

## Señales aleatorias

Realizaciones, estadística de registros, correlación y covarianza, modelos discretos estacionarios AR/MA/ARMA y ajuste AR mediante Yule–Walker. Los momentos teóricos del modelo y las estimaciones de un registro finito se presentan como objetos diferentes.

[Cobertura y temas pendientes →](scope/random-signals.md)

## Calculadora CAS

Hoja simbólica con expresiones, ecuaciones, matrices, supuestos y resultados reutilizables. Incluye operaciones de álgebra, cálculo y trigonometría. Cada salida puede referenciarse para continuar el cálculo, manteniendo la definición exacta cuando está disponible.

Las hipótesis y las condiciones de convergencia forman parte del resultado. Una expresión que el motor deja pendiente no se presenta como resuelta.
