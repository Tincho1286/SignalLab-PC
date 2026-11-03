# Transformada Z y expresiones con indeterminaciones

La transformada Z depende de la secuencia y de su soporte. En la directa, **0 a oo** representa una secuencia causal; **-oo a oo** incluye ambos lados del eje. Los índices son inclusivos y fuera del soporte indicado se considera cero.

## Completar una muestra y transformar la secuencia

SignalLab completa una indeterminación removible cuando los límites reales laterales coinciden y son finitos. Después separa ese valor del resto de la secuencia y aplica pares y propiedades antes de recurrir a la suma general. Un valor finito definido explícitamente en Por tramos se conserva.

Por ejemplo, `sin(pi*n)/(pi*n)` tiene valor 1 por continuidad en n=0 y vale 0 en todos los demás índices enteros. Por eso representa el impulso unitario y su transformada es **X(z)=1**, tanto con soporte de 0 a oo como de -oo a oo. Desplazar el impulso a n=d produce z^(-d).

La ruta por pares incluye exponenciales, senos y cosenos, potencias de n, potencias recíprocas, desplazamientos enteros y combinaciones lineales que puedan separarse sobre su soporte. Las series con 1/n pueden producir logaritmos; las potencias recíprocas de orden mayor pueden necesitar funciones especiales. Las condiciones de convergencia se conservan. El par logarítmico se basa en la [serie del logaritmo de NIST DLMF](https://dlmf.nist.gov/4.6.E1).

## La sinc que produce un pulso en frecuencia

Con 0 < wc < pi, la secuencia `sin(wc*n)/(pi*n)` tiene valor wc/pi en n=0. Su **DTFT bilateral** es un pulso periódico: vale 1 para |ω| < wc, 0 fuera de la banda y 1/2 en los saltos. Los desplazamientos enteros añaden el factor de fase correspondiente. Este par se describe en las [notas de DSP del IIT Bombay](https://www.ee.iitb.ac.in/~akumar/courses/ee603-2020/transforms.html).

Esa sinc bilateral no decrece exponencialmente en ninguna de las dos colas. Para |z| > 1 diverge la cola izquierda y para |z| < 1 diverge la derecha: no tiene una región **abierta** de convergencia para Z, aunque su DTFT exista sobre |z|=1. El informe muestra esta diferencia y, cuando reconoce el par, presenta también la DTFT. La sección Fourier permite calcularla y graficarla con soporte de -oo a oo.

Si se elige soporte de 0 a oo, se transforma sólo la mitad causal. Su Z tiene una expresión logarítmica y ROC exterior al círculo unitario; su respuesta no es el mismo pulso bilateral.

## Resultados pendientes y restricciones

No toda expresión admite una forma cerrada reconocida. Cuando las tablas y el motor general no resuelven un caso, el informe conserva la suma y lo identifica como pendiente. Una ROC vacía se identifica por separado. Los polos reales, las divergencias y los límites laterales distintos no se completan por continuidad.
