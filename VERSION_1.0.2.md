# SignalLab PC 1.0.2 · fórmulas de respuesta al impulso FIR

El informe del diseño FIR por especificaciones y por cortes muestra la respuesta ideal h_ideal[n], definida para todos los enteros, y la respuesta h[n] del filtro obtenido mediante ventana.

Se indican los cortes en rad/muestra, la convención sinc(x)=sin(πx)/(πx) con sinc(0)=1, la fórmula de la ventana elegida, L, M=L−1, el desplazamiento D=(L−1)/2, el soporte 0≤n≤L−1 y el factor de ganancia realmente aplicado. Para longitud par se evalúa el núcleo sinc entre índices, sin cambiar el eje discreto del filtro. Se cubren pasa bajos, pasa altos, pasa banda y rechaza banda, con ventanas rectangular, Hann, Hamming, Blackman, Bartlett y Kaiser.

El ideal no se confunde con las muestras truncadas: la gráfica existente conserva ese nombre y el informe explica su relación con el ideal infinito. Por especificaciones se informa la normalización aplicada; por cortes C=1. No se modifican los coeficientes ni el método de diseño. Ambos informes quedan disponibles en Resultados, con las fórmulas incluidas en el texto copiable y exportable.

Comprobación dirigida: las expresiones reproducen los coeficientes de los cuatro tipos y seis ventanas, incluidas longitudes pares donde corresponden; el caso Kaiser de 91 coeficientes conserva exactamente sus datos. Se revisaron el renderizado matemático y la ejecución del panel FIR. No se ejecutó una batería general.
