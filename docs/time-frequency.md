# Ventanas temporales y convolución por bloques

[← Herramientas](tools.md)

Estas ampliaciones están disponibles en la **1.8.4 preliminar**. Las operaciones trabajan con registros finitos y conservan el origen y el reloj de las salidas que se reutilizan.

## Leer un espectrograma

En **STFT y espectrograma**, elegí la longitud de ventana, el solapamiento y los puntos de FFT. La ventana es periódica, como corresponde al análisis espectral. Por defecto se completan ambos extremos del registro con ceros para que las ventanas también cubran sus bordes. Esto prepara el análisis del registro observado; no determina la señal real fuera de él.

El mapa ofrece cuatro escalas:

| Escala | Interpretación |
| --- | --- |
| Nivel relativo en dB | Compara cada celda con el máximo global de amplitud. |
| Amplitud lineal | Muestra `|FFT(x·w)| / Σw`. |
| Densidad bilateral | Muestra `|FFT(x·w)|² / (2π·Fs·Σw²)`. |
| Densidad en dB | Expresa esa densidad respecto de una unidad cuadrada por unidad de frecuencia angular. |

En rad/muestra se utiliza Fs=1. En rad/s se utiliza la tasa de muestras por segundo. La suma de densidad multiplicada por el paso angular coincide con la potencia del tramo ponderada por la ventana al cuadrado. No se resta la media ni se presenta un tramo como una estimación completa del proceso aleatorio.

El rango en dB modifica el piso visible. El informe y los valores complejos exportados conservan la definición original. La escala lineal no admite magnitudes fuera de float64; en ese caso se puede utilizar dB. Una matriz nula se identifica como tal y no produce densidades negativas.

## Elegir y reutilizar un tramo

Hacé clic sobre el mapa o utilizá el número de ventana y sus botones anterior/siguiente. Mientras está activo el zoom o el desplazamiento, los clics conservan su función de navegación. La franja clara marca la extensión temporal completa de la ventana seleccionada, incluyendo los ceros de análisis cuando corresponda.

En **Ventana seleccionada** se pueden consultar el espectro complejo, el tramo original, los pesos de la ventana, su producto y la densidad bilateral del tramo. Cada salida utiliza las acciones habituales de informe, gráfico, exportación, CAS y reutilización que correspondan a su tipo. Los registros conservan sus índices o tiempos originales.

La fase del espectro puede referirse al origen del registro o al comienzo local del tramo. En el primer caso se incluye el desplazamiento temporal; en el segundo, el índice local empieza en cero. El selector no cambia el módulo ni la densidad. Exportar la STFT completa guarda las unidades y la referencia de fase elegidas junto con sus valores complejos.

## Segundos y frecuencia angular física

Una secuencia con Fs registrada permite elegir **Segundos y rad/s** en la figura. Se utiliza el tiempo de la primera muestra si está guardado; si sólo existe Fs, la referencia es t=n/Fs. Sin reloj, la secuencia conserva índices y rad/muestra. Los registros continuos ya utilizan segundos y rad/s.

Cambiar la vista no remuestrea la señal. Las columnas reutilizadas y el CSV adoptan las unidades elegidas. Una densidad por rad/s incluye el factor de escala correspondiente; no basta con cambiar la etiqueta del eje.

## Reconstruir desde la STFT

**Reconstrucción → Reconstruir registro desde STFT** aplica IFFT, pondera y suma los tramos y divide por la suma de ventanas al cuadrado. La salida recupera la longitud, el origen y el reloj del registro. El informe muestra la cobertura mínima y una medida del error respecto de la entrada almacenada.

La cobertura se comprueba sobre todas las muestras. Una ventana que se anula en el borde puede perder información si no se completan los extremos; un salto demasiado grande también puede dejar huecos. En esos casos no se publica una reconstrucción completa ficticia: se indican las muestras afectadas y se propone completar los extremos o aumentar el solapamiento. El umbral también evita dividir por coberturas numéricamente insignificantes.

## Inspeccionar OLA y OLS

Después de calcular **Convolución por bloques**, abrí **Inspeccionar bloques**. El navegador permite recorrer los bloques y elegir su entrada, salida FFT, contribución válida y salida total en el mismo intervalo.

En **solapamiento-suma (OLA)**, cada bloque aporta su convolución lineal y su cola se suma a las contribuciones vecinas. Esa contribución puede diferir de la salida total en los mismos índices; no es un error ni se descarta la cola.

En **solapamiento-almacenamiento (OLS)**, la entrada incluye M−1 muestras de historia. Se descartan las primeras M−1 salidas circulares y se conservan las L nuevas, o las que faltan de la cola final. La figura distingue las muestras descartadas de los puntos FFT finales no utilizados. Los datos reutilizados mantienen esos índices y describen su función en los metadatos.

Estas convenciones siguen la reconstrucción por suma ponderada y la condición de cobertura no nula descritas en la [referencia de NOLA de SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.check_NOLA.html). La [referencia de Welch](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.welch.html) explica la distinción entre espectro y densidad; aquí la densidad se expresa por frecuencia angular y conserva ambas mitades del espectro.
