# Contratos científicos de canal

## Multitrayecto determinista LTI

`ChannelPath` describe un retardo entero no negativo en muestras y una ganancia compleja finita. `MultipathSpec` contiene un conjunto ordenado de trayectorias y la opción booleana de normalización. La aplicación acepta la tupla histórica como una configuración sin normalización.

Se suman las ganancias de trayectorias que comparten retardo antes de calcular la salida y el perfil. Por ejemplo, dos trayectorias de ganancia 1 al mismo retardo producen potencia 4 en ese instante. Ganancias opuestas se cancelan. Las muestras fuera del registro se consideran cero. Se conserva el soporte de salida declarado por el mayor retardo, incluso si ese tap se anula.

La respuesta impulsional se entrega en forma dispersa `(retardo, ganancia)`. Sus potencias están en unidades lineales como módulo cuadrado de la ganancia. El promedio de los retardos y la desviación RMS usan esas potencias como pesos. Los momentos de una respuesta nula quedan indefinidos. La normalización opcional fija la suma de potencias de la respuesta impulsional en uno. Una respuesta nula produce un error si se pide normalizar.

Con L muestras por símbolo, el análisis toma como referencia el tap coherente de mayor potencia, el primero en caso de empate. Suma las potencias de los demás taps que coinciden con esa fase de muestreo y divide por la potencia de referencia. Es una medida de ISI del canal a intervalos de símbolo, sin el efecto de los pulsos TX/RX ni de la sincronización. Los tiempos físicos se obtienen dividiendo los retardos en muestras por Fs.

`multipath_frequency` evalúa $H(e^{j\omega}) = \sum_d h[d]e^{-j\omega d}$ en las frecuencias periódicas de una DFT centrada. El algoritmo reduce cada retardo módulo N antes de formar las fases, de modo que los retardos enteros grandes preservan la periodicidad en esos puntos. El resultado usa rad/muestra y convención de frecuencia angular. [Modelo de banda base](https://web.stanford.edu/~dntse/papers/ch1%2B2.pdf).

El resultado temporal usa metadatos `communications_multipath` esquema 2, con la configuración original, su indicador de normalización y la huella de la señal de entrada. Los resultados escritos con esquema 1 conservan su representación histórica. La normalización opera sobre el modelo, de modo que se aplica también a sus diagnósticos.

## Fading Rayleigh/Rician independiente

`FadingSpec` contiene una semilla entera y una secuencia de `FadingPath`. Cada camino tiene retardo entero $d$, potencia media lineal $P$, relación LOS/NLOS $K$ y fase LOS $\phi$ en radianes. La escala dB para K usa $K=10^{K_{dB}/10}$. K lineal cero representa Rayleigh y la fase LOS pierde efecto.

Para un camino, se genera $a[n] = \sqrt{PK/(1+K)}\exp(j\phi) + \sqrt{P/(2(1+K))}(X[n]+jY[n])$, con X e Y normales estándar independientes. La potencia media esperada es P. El coeficiente vive en el índice de llegada y multiplica $x[n-d]$. Los caminos tienen flujos PCG64 independientes derivados de la semilla con `SeedSequence.spawn`. Su orden forma parte de la configuración registrada. Se admite un camino para fading plano o varios caminos retardados para variación selectiva. Las contribuciones coincidentes se suman coherentemente en el registro. Si varios caminos Rician coinciden en retardo, la potencia esperada del tap suma las varianzas dispersivas y el módulo cuadrado de la suma de sus medias LOS.

La salida conserva el índice inicial, el reloj y el mayor retardo. El resultado incluye los coeficientes de cada camino y la media y potencia observadas durante su tramo activo. Los coeficientes empiezan en el índice de llegada del primer punto del registro, con unidades de amplitud adimensionales. El esquema 1 registra proceso `iid`, versión NumPy, generador, parámetros y huella de entrada. [Fundamento](https://web.stanford.edu/~dntse/papers/ch1%2B2.pdf) · [Contrastes](MATHEMATICAL_AUDIT.md)
