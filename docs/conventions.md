# Convenciones matemáticas

[← Documentación](README.md)

## Tiempo e índices

En una secuencia discreta, n es entero. El origen indica la posición de la primera muestra y no la cantidad de datos. Un registro finito vale cero fuera de su soporte cuando el método así lo declara; no se supone una repetición periódica.

Las señales continuas numéricas se describen mediante un registro de tiempo y un modelo de integración o interpolación. Una muestra ordinaria no es una Dirac: los impulsos continuos se conservan por posición y peso.

## Fourier

- DFT directa sin factor de normalización; IDFT con factor 1/N.
- DTFT en rad/muestra, periódica cada 2π.
- Fourier continua en rad/s; la inversa angular usa el factor 1/(2π).
- Agregar ceros a una FFT densifica el muestreo de frecuencia, sin ampliar la duración observada.

Las muestras DFT y la curva DTFT se comparan usando las mismas coordenadas y el origen de la secuencia. Las ventanas y cuadraturas finitas conservan su alcance de aproximación.

## Transferencias y ROC

En H(s), los coeficientes se ordenan por potencias descendentes de s. En H(z), se usa el orden 1, z⁻¹, z⁻², …; las fórmulas también pueden conservar avances temporales.

La fracción racional y su región de convergencia determinan una transformada bilateral. Un mismo cociente puede corresponder a una señal derecha, izquierda o de dos lados. La respuesta en frecuencia como transformada de Fourier requiere que el eje imaginario, o el círculo unitario en discreto, pertenezca a la ROC.

La simplificación de una transferencia no demuestra estabilidad interna de una realización con cancelaciones. Las raíces se representan numéricamente y los órdenes altos o raíces múltiples pueden ser sensibles al redondeo.

## Ventanas y FIR

L es la cantidad total de coeficientes y M=L−1 el orden nominal. El centrado del ideal causal usa D=(L−1)/2. Las ventanas de generación son simétricas; con longitud par el centro geométrico puede ser semientero aunque los índices sigan siendo enteros.

Se usa sinc(x)=sin(πx)/(πx), con sinc(0)=1. En la preliminar 1.2, la capa matemática extiende singularidades removibles cuando demuestra límites laterales finitos e iguales; los polos y las divergencias no reciben valores arbitrarios.

## Tolerancias por banda en 1.2

Para una amplitud de paso A, las tolerancias absolutas definen [A−δp,A+δp], las relativas [A(1−δp),A(1+δp)] y el rizado ±rp dB define [A·10^(−rp/20),A·10^(rp/20)].

El rechazo absoluto se limita por δs. En modo relativo o en dB se usa Aref, la mayor amplitud de paso: Aref·δs o Aref·10^(−As/20). Un rechazabanda FIR puede tener amplitudes inferiores y superiores diferentes; las familias IIR clásicas requieren una ganancia común.

La evaluación sobre frecuencias y bordes forma parte del diseño. Un resultado fuera de tolerancias se identifica expresamente; una rejilla no certifica máximos continuos entre sus puntos.

## Exactitud y presentación

Los informes distinguen expresiones exactas, aproximaciones numéricas, condiciones y cálculos pendientes. El formato visual puede redondear cifras para facilitar la lectura; la exportación conserva los valores almacenados. Un resultado de una ventana finita no demuestra propiedades de una señal infinita.
