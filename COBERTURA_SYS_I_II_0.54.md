> Referencia histórica: este documento conserva el estado de su fecha. Para prioridades y evidencia vigentes, consultar [CIERRE_1.0.md](CIERRE_1.0.md) y [README.md](README.md). Algunas carencias aquí mencionadas fueron cubiertas después; no es una lista actual de bloqueos.

> Alcance actualizado 0.57: modulación y demodulación excluidas por el usuario. Prioridad actual: importación MATLAB, optimización y revisión de las herramientas existentes. Ver DESARROLLO_0.57.md.

# Sistemas y Señales I y II · trabajo hacia la primera estable

Revisión: 25/10/2026. Base: programas 2026 aportados por el usuario, inventario de rutas y código actual. Se revisaron las páginas de contenidos de Sistemas I (incluyendo 6, 9, 12, 13 y 14) y los ejes analíticos de Sistemas II. Es una revisión temática, no una certificación de todos los ejercicios.

## Prioridades acordadas

- El usuario confirma que el portable funciona: se toma ese punto como validado por él y no se repite una campaña de instalación.
- El usuario asume la revisión general de interfaz y reutilización. Las correcciones concretas que reporte se atienden durante el desarrollo.
- Persistencia, validación general y ayuda se mejorarán gradualmente; no detienen esta etapa de ampliación funcional.
- Esta etapa se limita a Sistemas y Señales I y II. No se amplía Señales Aleatorias; las funciones existentes se conservan.

## Carencias cubiertas en 0.54

| Programa | Tema explícito | Incorporación |
|---|---|---|
| Sistemas I, 7.6 | Hilbert, preenvolvente y aplicaciones | Hilbert numérica, señal analítica y envolvente; admite secuencias y registros continuos muestreados reales. No es una transformada simbólica general. |
| Sistemas II, 3.4 | Convolución por bloques, solapamiento-suma y solapamiento-almacenamiento | Ambos métodos FFT, con tamaño de bloque configurable, informe del solapamiento y salida completa de N+M−1 muestras. |
| Sistemas II, 5.3 | Fourier dependiente del tiempo y espectrograma | STFT de ventanas solapadas, mapa en frecuencia angular, espectros de cada ventana y exportación CSV de la matriz compleja completa. |
| Sistemas II, 7.4 | Ventana Bartlett | Disponible en FIR, FIR por especificaciones, análisis de ventanas/FFT y STFT. |

La STFT muestra un nivel relativo al máximo global, no una PSD calibrada. La normalización, la fase local y el relleno final se explican en el informe. La sesión conserva el informe y los espectros locales consultados; para conservar la matriz completa se debe usar Exportar STFT completa. La convolución supone extensión por ceros; Hilbert supone extensión periódica del registro.

## Cobertura ya presente

| Área | Herramientas disponibles | Límite relevante |
|---|---|---|
| Señales y transformaciones | Fórmulas/tramos, muestras, inversión, desplazamiento, escala temporal, par/impar, energía y potencia | Registros finitos en el cálculo numérico; los análisis globales tienen sus propias condiciones. |
| Sistemas LTI | Transferencias, convolución/correlación, impulso/escalón, respuesta temporal, interconexiones, raíces y estabilidad | No equivale a demostrar propiedades de cualquier operador no lineal definido por el usuario. |
| Series/Fourier | Series continuas/discretas, DFT/DTFT, Fourier continua numérica y algebraica, densidades, Parseval por sus resultados | Las distribuciones simbólicas no son muestras de altura finita. |
| Laplace/Z | Laplace unilateral, inversa causal, Z finita, inversa racional y contornos con ROC | No es un analizador bilateral general de todas las expresiones y regiones. |
| Muestreo | Muestreo, aliasing, reconstrucción, diezmado/interpolación, cambio racional, cuantización y punto fijo | Registros finitos; no simulación completa del hardware A/D y de todas las estructuras aritméticas. |
| FIR/IIR | Ventanas, especificaciones, raíces, familias digitales y conversión de transferencias | La búsqueda de longitud FIR no demuestra mínimo global; queda ampliar la experiencia analógica. |
| Control | Realimentación, lugar de raíces, estados, respuesta temporal/frecuencial | La presencia de estas operaciones no certifica todos los ejercicios de control del programa. |

## Siguientes herramientas o ampliaciones, sólo I y II

1. **Diseño analógico por especificaciones:** interfaz común para Butterworth, Chebyshev y elípticos, con frecuencias en rad/s; ampliar realizaciones físicas de órdenes superiores. Hoy hay RC, segundo orden, transferencias y ciertos prototipos de conversión.
2. **Diagramas de realización:** estructuras directas, cascada y paralelo de ecuaciones/transferencias. Conectar bloques H no reemplaza mostrar retardos, sumadores y multiplicadores de una realización.
3. **Relaciones módulo–fase y compensación:** reconstrucción y análisis específico bajo las condiciones correspondientes; existe descomposición de fase mínima/paso todo, pero no toda la temática del eje 6.
4. **Modulación y demodulación AM:** se pueden construir señales con fórmulas y filtrar; falta un recorrido dedicado de comparación entre señal modulada, portadora y señal recuperada (Sistemas I, 7.4).
5. **Muestreo pasabanda:** completar una herramienta que determine intervalos admisibles de tasa para bandas dadas; el laboratorio general de aliasing no cubre por sí solo esa selección.
6. **Transformadas y propiedades:** ampliar transformadas bilaterales/ROC y facilitar verificaciones de ortogonalidad y propiedades a partir de señales propias, sin confundir ejemplos finitos con demostraciones.
7. **Aritmética de implementación:** ampliar efectos de cuantización de coeficientes, estructuras y representación flotante; el módulo actual de punto fijo es parcial.

No se incorporan ahora detectores, Wiener/Kalman, ARMA ni procesos de Markov/Poisson de la materia Señales Aleatorias.

## Corrección adicional solicitada durante esta entrega

El lector compartido de coeficientes numéricos admite expresiones constantes: pi, 2*pi, 10^(-6), 10**(-6), 1e-6 y complejos. Se elimina el reemplazo indiscriminado de i por j que corrompía pi. Una celda vacía genera un mensaje con su posición; no se elimina silenciosamente alterando el orden. Los coeficientes numéricos no admiten variables libres.

## Comprobación acotada realizada

- OLA y OLS contra convolución directa en una secuencia compleja corta, con tres tamaños de bloque, cola completa y origen no nulo.
- Hilbert de una sinusoidal periódica contra su exponencial compleja.
- Frecuencia y amplitud de un tono complejo en una STFT rectangular.
- Apertura y cálculo de los tres paneles nuevos y construcción de su ayuda.
- Lectura de pi, potencias, notación científica y complejos en el lector de coeficientes.

No se repitieron pruebas generales de interfaz ni de instalación del portable. La entrega añade un bloque concreto hacia 1.0; aún no declara cobertura completa.

Referencias técnicas utilizadas: [SciPy Hilbert](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.hilbert.html), [ventanas SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.windows.get_window.html). La STFT implementada declara su propia normalización en el informe; no se presenta como equivalente a una densidad espectral calibrada.
