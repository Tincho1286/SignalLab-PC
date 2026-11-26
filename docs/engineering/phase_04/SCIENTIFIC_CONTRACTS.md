# Contratos científicos de canal

## Multitrayecto determinista LTI

`ChannelPath` describe un retardo entero no negativo en muestras y una ganancia compleja finita. `MultipathSpec` contiene un conjunto ordenado de trayectorias y la opción booleana de normalización. La aplicación acepta la tupla histórica como una configuración sin normalización.

Se suman las ganancias de trayectorias que comparten retardo antes de calcular la salida y el perfil. Por ejemplo, dos trayectorias de ganancia 1 al mismo retardo producen potencia 4 en ese instante. Ganancias opuestas se cancelan. Las muestras fuera del registro se consideran cero. Se conserva el soporte de salida declarado por el mayor retardo, incluso si ese tap se anula.

La respuesta impulsional se entrega en forma dispersa `(retardo, ganancia)`. Sus potencias están en unidades lineales como módulo cuadrado de la ganancia. El promedio de los retardos y la desviación RMS usan esas potencias como pesos. Los momentos de una respuesta nula quedan indefinidos. La normalización opcional fija la suma de potencias de la respuesta impulsional en uno. Una respuesta nula produce un error si se pide normalizar.

Con L muestras por símbolo, el análisis toma como referencia el tap coherente de mayor potencia, el primero en caso de empate. Suma las potencias de los demás taps que coinciden con esa fase de muestreo y divide por la potencia de referencia. Es una medida de ISI del canal a intervalos de símbolo, sin el efecto de los pulsos TX/RX ni de la sincronización. Los tiempos físicos se obtienen dividiendo los retardos en muestras por Fs.

`multipath_frequency` evalúa $H(e^{j\omega}) = \sum_d h[d]e^{-j\omega d}$ en las frecuencias periódicas de una DFT centrada. El algoritmo reduce cada retardo módulo N antes de formar las fases, de modo que los retardos enteros grandes preservan la periodicidad en esos puntos. El resultado usa rad/muestra y convención de frecuencia angular. [Modelo de banda base](https://web.stanford.edu/~dntse/papers/ch1%2B2.pdf).

El resultado temporal usa metadatos `communications_multipath` esquema 2, con la configuración original, su indicador de normalización y la huella de la señal de entrada. Los resultados escritos con esquema 1 conservan su representación histórica. La normalización opera sobre el modelo, de modo que se aplica también a sus diagnósticos.

## Fading Rayleigh/Rician

`FadingSpec` contiene una semilla entera y una secuencia de `FadingPath`. Cada camino tiene retardo entero $d$, potencia media lineal $P$, relación LOS/NLOS $K$ y fase LOS $\phi$ en radianes. La escala dB para K usa $K=10^{K_{dB}/10}$. K lineal cero representa Rayleigh y la fase LOS pierde efecto.

Para un camino, se genera $a[n] = \sqrt{PK/(1+K)}\exp(j\phi) + \sqrt{P/(2(1+K))}(X[n]+jY[n])$, con X e Y normales estándar independientes. La potencia media esperada es P. El coeficiente vive en el índice de llegada y multiplica $x[n-d]$. Los caminos tienen flujos PCG64 independientes derivados de la semilla con `SeedSequence.spawn`. Su orden forma parte de la configuración registrada. Se admite un camino para fading plano o varios caminos retardados para variación selectiva. Las contribuciones coincidentes se suman coherentemente en el registro. Si varios caminos Rician coinciden en retardo, la potencia esperada del tap suma las varianzas dispersivas y el módulo cuadrado de la suma de sus medias LOS.

La salida conserva el índice inicial, el reloj y el mayor retardo. El resultado incluye los coeficientes de cada camino y la media y potencia observadas durante su tramo activo. Los coeficientes empiezan en el índice de llegada del primer punto del registro, con unidades de amplitud adimensionales. El proceso `iid` genera las normales directamente por muestra. El esquema 2 registra el proceso, generador, versiones numéricas, configuración, huella de entrada y parámetros de cuadratura cuando corresponden. Los registros previos de esquema 1 conservan sus datos. [Fundamento](https://web.stanford.edu/~dntse/papers/ch1%2B2.pdf) · [Contrastes](MATHEMATICAL_AUDIT.md)

### Dispersión Doppler de Clarke

`FadingSpec.max_doppler_hz` vacío selecciona coeficientes independientes. Un Doppler máximo $f_D > 0$ requiere un reloj con $f_D < F_s/2$. En el modelo Clarke cada cuadratura es gaussiana y correlacionada en el tiempo e independiente de la otra. Su densidad continua normalizada es $S(f) = 1 / (\pi f_D\sqrt{1-(f/f_D)^2})$ para $|f|<f_D$. La autocorrelación normalizada es $J_0(2\pi f_D\tau)$. En Rician se compara la componente difusa después de restarle la media LOS configurada.

La realización integra la masa teórica de cada uno de $M=\max(64,\lceil 8Nf_D/F_s\rceil)$ intervalos uniformes y la representa mediante una línea aleatoria en el punto medio. La señal usa coeficientes gaussianos complejos independientes por intervalo, ponderados con la raíz de su masa. Zoom FFT evalúa las líneas en los instantes del registro. Se conserva la potencia esperada, con una aproximación discreta de la forma espectral. Para un retardo $\ell$ la diferencia entre la autocorrelación normalizada de cuadratura y la continua está acotada por $2\pi f_D |\ell|/(F_s M)$. El error observado también incluye la variación de la estimación de una realización finita.

Con $f_D=0$ la ganancia es aleatoria y fija durante el registro. Las líneas de la cuadratura mínima se colapsan en CC con los mismos pesos, de modo que un registro de longitud fija converge al caso de cero con la misma semilla cuando $f_D$ tiende a cero. El tiempo de coherencia es el primer cruce de 0,5 de la autocorrelación teórica difusa e infinito para $f_D=0$.

La API y CLI generan la autocorrelación observada normalizada por la potencia difusa del registro y la PSD Welch bilateral en 1/Hz. La referencia espectral muestra la masa Clarke dividida por el ancho de cada bin, incluido el caso de CC. En Workbench se muestra el diagnóstico de la primera trayectoria con potencia. [Clarke](https://web.stanford.edu/~dntse/papers/main.pdf) · [Zoom FFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ZoomFFT.html).

## Desplazamiento determinista de frecuencia y fase

`CarrierShift` multiplica cada muestra por $\exp(j(2\pi\Delta f\,k/F_s + \phi))$, con k contado desde cero a partir de la primera muestra. El signo positivo aumenta la frecuencia. Un desplazamiento no nulo exige el reloj y $|\Delta f|<F_s/2$. En tiempo discreto el espectro se desplaza con periodicidad Fs. Se conservan magnitud, índices, reloj y unidades. El modelo sirve para Doppler determinista o CFO y mantiene una fase de referencia explícita. El resultado registra los dos parámetros en SI y la huella del origen.
