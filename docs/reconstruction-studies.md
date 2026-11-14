# Comparar e inspeccionar reconstrucciones

La **1.8.13 preliminar** amplía **Muestreo y A/D → Reconstruir una señal**. Reúne ZOH, lineal y SINC sobre las mismas muestras, con un reloj común. El selector del área de resultados permite superponer métodos o elegir una reconstrucción, referencia o curva de error para exportarla, enviarla al CAS o utilizarla en otra herramienta.

## Reloj y ventana

Cargá una secuencia desde una fórmula, muestras, un archivo o Resultados. Fs indica muestras por segundo y t₀ es el tiempo de la primera muestra guardada. Un índice original n₀ distinto de cero no desplaza ese instante automáticamente: t[k]=t₀+k/Fs, con k contando posiciones locales desde cero.

Si la entrada conserva su reloj, se utiliza ese dato. Reinterpretar permite sustituirlo de manera explícita. Las subdivisiones L determinan el paso de dibujo 1/(L·Fs); no agregan información a las muestras originales. Los períodos antes y después amplían la ventana en unidades de 1/Fs.

## Tres núcleos y sus bordes

La reconstrucción es la suma xᵣ(t)=Σ x[k]·p(Fs·(t−t₀)−k), sobre las muestras guardadas. La secuencia se extiende por cero fuera de ese registro.

- ZOH usa p(u)=1 para 0≤u<1. Retiene cada muestra un período, incluida la última.
- Lineal usa p(u)=max(1−|u|,0). Tiene una rampa desde cero antes de la primera muestra y hacia cero después de la última.
- SINC usa p(u)=sin(πu)/(πu), con valor 1 en cero. Incluye todas las muestras del registro y sus colas continúan fuera de la ventana dibujada. Sus pesos no se renormalizan.

Con cero períodos adicionales se muestra desde el primer hasta el último nudo, como en la herramienta anterior. Agregar un período a cada lado revela los bordes de ZOH y lineal. Ampliar más la ventana permite explorar las colas SINC. No cambia los datos ni inventa observaciones fuera del registro.

SINC utiliza suma directa compensada en los casos pequeños o con amplitudes que no admiten una escala común segura. Para registros grandes utiliza convolución FFT y conserva los nudos originales por construcción. El informe identifica el procedimiento. El inspector evalúa el mismo núcleo mediante suma directa; una diferencia de redondeo no sustituye la curva guardada.

## Referencia y medidas de error

Comparar con una referencia permite ingresar r(t), evaluada en la misma rejilla temporal. El error es xᵣ−r. El informe muestra su RMS, máximo módulo y SNR mediante la relación entre las sumas cuadráticas de referencia y error.

Estas medidas asignan igual peso a todos los puntos, con ambos extremos incluidos. No se presentan como una integral continua del error. Un error nulo con referencia no nula corresponde a SNR +∞; referencia y error nulos no definen esa relación. Una referencia que no pueda evaluarse queda identificada en el informe y las reconstrucciones siguen disponibles.

## Nudos y aportes por muestra

Nudos originales muestra la diferencia entre cada reconstrucción y la entrada en las posiciones de las muestras. Los núcleos son cardinales y el método FFT restaura esos puntos por construcción. Por eso un desvío cero no demuestra que no haya aliasing ni que se haya recuperado la señal infinita de origen.

Aportes por muestra permite elegir un instante y un método. La tabla conserva el índice original, el tiempo, el valor, el peso del núcleo y su contribución. Se publican también los pesos y, cuando pueden representarse, los aportes como secuencias. El inspector puede evaluar instantes entre puntos o fuera de la ventana mostrada; utiliza el modelo y reloj del último cálculo.

Editar una entrada conserva el resultado anterior hasta recalcular. Evaluar un instante no vuelve a reconstruir todas las curvas. Cambiar el método de una curva individual y el del inspector conserva la selección correspondiente.

## Exportar y continuar

Cada curva y el informe completo quedan en Resultados. Exportar una comparación guarda todos sus miembros con sufijos numéricos, un archivo por curva; no limita la salida a dos señales. Las tablas de nudos y aportes ofrecen CSV con el reloj y el contexto de la medida. Los gráficos se abren desde la cabecera de resultados y mantienen sus ejes temporales comunes.
