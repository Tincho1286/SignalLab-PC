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

En **DFT → Transformada directa**, **Referencia de fase** permite elegir los índices de la señal o las posiciones del registro. Por defecto se usan los índices `n=n₀+m`, lo que hace coincidir la DFT con la DTFT en los bins. **Primera muestra del registro** toma `m=0` como referencia y reproduce la convención anterior. El factor que convierte esa DFT a fase en `n` es `exp(−j2πkn₀/N)`.

Los resultados JSON y CSV de SignalLab guardan la referencia de fase y el índice inicial. Al cargar una DFT, la inversa recupera el orden de las muestras según esa referencia. **Restaurar el índice inicial** decide si el eje comienza en el índice guardado o en cero. Las DFT directas guardadas antes de esta distinción y las listas manuales conservan la convención con fase referida a la primera muestra.

En **Ventanas y resolución**, el espectro centrado respeta los índices `n`. El resultado con `k` desde cero conserva la referencia a la primera muestra. Las ventanas y cuadraturas finitas conservan su alcance de aproximación.

## Transferencias y ROC

En H(s), los coeficientes se ordenan por potencias descendentes de s. En H(z), se usa el orden 1, z⁻¹, z⁻², …; las fórmulas también pueden conservar avances temporales.

La fracción racional y su región de convergencia determinan una transformada bilateral. Un mismo cociente puede corresponder a una señal derecha, izquierda o de dos lados. La respuesta en frecuencia como transformada de Fourier requiere que el eje imaginario, o el círculo unitario en discreto, pertenezca a la ROC.

La simplificación de una transferencia no demuestra estabilidad interna de una realización con cancelaciones. Las raíces se representan numéricamente y los órdenes altos o raíces múltiples pueden ser sensibles al redondeo.

## Ventanas y FIR

L es la cantidad total de coeficientes y M=L−1 el orden nominal. El centrado del ideal causal usa D=(L−1)/2. Las ventanas de generación son simétricas; con longitud par el centro geométrico puede ser semientero aunque los índices sigan siendo enteros.

Se usa sinc(x)=sin(πx)/(πx), con sinc(0)=1. La capa matemática extiende singularidades removibles cuando demuestra límites laterales finitos e iguales; los polos y las divergencias no reciben valores arbitrarios.

## Tolerancias por banda

Para una amplitud de paso A, las tolerancias absolutas definen [A−δp,A+δp], las relativas [A(1−δp),A(1+δp)] y el rizado ±rp dB define [A·10^(−rp/20),A·10^(rp/20)].

El rechazo absoluto se limita por δs. En modo relativo o en dB se usa Aref, la mayor amplitud de paso: Aref·δs o Aref·10^(−As/20). Un rechazabanda FIR puede tener amplitudes inferiores y superiores diferentes; las familias IIR clásicas requieren una ganancia común.

La evaluación sobre frecuencias y bordes forma parte del diseño. Un resultado fuera de tolerancias se identifica expresamente; una rejilla no certifica máximos continuos entre sus puntos.

## Exactitud y presentación

Los informes distinguen expresiones exactas, aproximaciones numéricas, condiciones y cálculos pendientes. El formato visual puede redondear cifras para facilitar la lectura; la exportación conserva los valores almacenados. Un resultado de una ventana finita no demuestra propiedades de una señal infinita.

### Reloj de los registros discretos

`time_start_s` identifica el instante de la muestra almacenada en `origin`.
Con `sample_rate_hz`, el resto del registro sigue
`t = time_start_s + (n - origin) / sample_rate_hz`. Puede conocerse la tasa
sin conocer ese instante. Las unidades del eje (`n`, segundos o frecuencia)
describen las coordenadas; no especifican unidades de amplitud.

- La suma alinea índices. Si ambas tasas están registradas, deben coincidir.
  Si también se conocen ambos instantes, deben identificar la misma rejilla.
  Si falta una tasa se conserva el resultado en índices, sin asignarle un
  reloj compartido. Dos tasas válidas permiten conservar Fs aunque falte
  un instante.
- El producto conserva la rejilla de la primera entrada. Una segunda
  secuencia definida en índices actúa como máscara sobre esa rejilla. Si
  ambas entradas traen reloj, se comprueba la misma alineación que en la suma.
- En convolución lineal se suman los tiempos iniciales. En correlación
  lineal se restan y se considera el primer retardo publicado
  (`nₓ − nₕ − (Nₕ − 1)`). Los instantes requieren dos relojes disponibles.
  La variante circular conserva la convención de índices periódicos de cada
  operación; su referencia temporal se interpreta módulo el período.
- Cambiar la tasa transforma Fs y ajusta el primer instante cuando se conoce.
  El cambio racional permite dejar ese instante sin definir o indicarlo
  explícitamente.
- Extraer un tramo conserva el orden y el paso del registro. En discreto, el
  nuevo instante inicial se obtiene del desplazamiento en muestras si se
  conocen Fs y el instante original. Si se mueve el inicio y falta alguno de
  esos datos, el nuevo instante queda sin definir.
- Un filtro discreto puede aportar la tasa a la entrada sin fijar el instante
  de la primera muestra. Si una STFT solo conoce la tasa, muestra segundos
  relativos a la primera muestra y no asigna tiempos absolutos a sus tramos.
  Una simulación discreta multicanal exige que coincidan los instantes
  registrados y conserva un inicio físico cuando todas las entradas lo indican.


## Transferencia en el plano complejo

H(s) y H(z) se presentan mediante mallas de sus partes real/imaginaria o módulo/ángulo. Las coordenadas del plano son independientes de la altura de la componente. El ángulo principal está entre −π y π y sus saltos no se unen. La respuesta en frecuencia usa su propio recorrido y puede mostrar ángulo desenrollado por tramos válidos.
