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

La API y CLI generan la autocorrelación observada normalizada por la potencia difusa del registro y la PSD Welch bilateral en 1/Hz. La referencia espectral muestra la masa Clarke dividida por el ancho de cada bin, incluido el caso de CC. Workbench usa la trayectoria elegida o la primera con potencia. [Clarke](https://web.stanford.edu/~dntse/papers/main.pdf) · [Zoom FFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ZoomFFT.html).

### Distribuciones de envolvente y fase

El diagnóstico divide el módulo de los coeficientes por $\sqrt P$. Para Rician, calcula el ángulo respecto de la fase LOS y lo sitúa en $[-\pi,\pi)$. Para Rayleigh usa la fase absoluta. El histograma divide cada recuento por el número de muestras y el ancho del intervalo. Las referencias usan $\mu=\sqrt{K/(1+K)}$ y $\sigma=1/\sqrt{2(1+K)}$ para la variable compleja normalizada.

La envolvente tiene densidad Rice con parámetro de forma $\mu/\sigma$ y escala $\sigma$. Cuando K = 0 se reduce a Rayleigh. La densidad de fase se obtiene integrando la gaussiana bidimensional sobre el radio. Con $\eta=\sqrt{2K}\cos\theta$ es $e^{-K}/(2\pi)+\eta e^{-K\sin^2\theta}\Phi(\eta)/\sqrt{2\pi}$, donde $\Phi$ es la CDF normal estándar. Cuando K = 0, la fase es uniforme. [Densidad Rice](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.rice.html) · [Oráculos independientes](MATHEMATICAL_AUDIT.md#protocolo-para-las-distribuciones-visuales-de-fading).

Las curvas se evalúan en una grilla independiente del histograma para resolver picos angostos. Se muestran en un intervalo de hasta ocho desviaciones por cuadratura alrededor de la media radial o de la fase dominante, y para K ≤ 10 se muestra toda la fase. El diagnóstico avisa si la concentración queda por debajo de la resolución del gráfico. Una trayectoria sin potencia carece de diagnóstico. Con Doppler nulo, toda la realización comparte un coeficiente y su histograma se concentra en un intervalo. Con Doppler positivo, la comparación describe la distribución marginal y el histograma de un registro correlacionado puede apartarse de la referencia.

## Desplazamiento determinista de frecuencia y fase

`CarrierShift` multiplica cada muestra por $\exp(j(2\pi\Delta f\,k/F_s + \phi))$, con k contado desde cero a partir de la primera muestra. El signo positivo aumenta la frecuencia. Un desplazamiento no nulo exige el reloj y $|\Delta f|<F_s/2$. En tiempo discreto el espectro se desplaza con periodicidad Fs. Se conservan magnitud, índices, reloj y unidades. El modelo sirve para Doppler determinista o CFO y mantiene una fase de referencia explícita. El resultado registra los dos parámetros en SI y la huella del origen.

## Retardo y desajuste del reloj

`TimingOffset` conserva la ventana del receptor de N muestras. Con retardo $d$ medido en muestras de entrada y error $p$ en ppm, cada salida se evalúa en la coordenada $k/(1+p\,10^{-6})-d$. Un retardo positivo demora la entrada dentro de la ventana y un error positivo aumenta la tasa de salida. Los índices externos al registro de entrada se tratan como muestras nulas. El número de muestras y el primer instante del receptor se conservan, por lo que la duración física cambia con Fs. Con retardo entero y SFO cero, el desplazamiento se calcula mediante índices exactos.

Los instantes no enteros se aproximan con sinc de ventana Lanczos. La frecuencia de corte relativa a la Nyquist de entrada es $\min(1, F_{s,\text{salida}}/F_{s,\text{entrada}})$. Se escala la semilongitud de 32 muestras al reducir la tasa. El núcleo se normaliza para reproducir una constante lejos de los bordes. El FIR tiene transición finita y su error crece cerca de Nyquist y de los bordes del registro. El informe de auditoría documenta el error para el perfil y los tonos efectivamente probados.

El reloj de símbolos físico se conserva. Si la nueva tasa implica un intervalo fraccionario por símbolo, se retira el campo entero `samples_per_symbol`. El receptor de Fase 03 detecta que la tasa del registro es incompatible con su captura a paso entero. Este modelo introduce el deterioro, con recuperación pendiente de integración.

## Ruido de fase Wiener

`PhaseNoiseSpec.linewidth_hz` fija el ancho completo a media altura de una línea lorentziana en el modelo continuo. En discreto, la fase inicial es cero y los incrementos por muestra son gaussianos independientes con varianza $2\pi\Delta\nu/F_s$ en rad². Se guarda tanto la señal rotada como una realización de la fase sin envolver. La amplitud y el reloj se conservan. Ancho cero conserva la señal y no requiere una Fs. El esquema registra semilla, generador PCG64, versión NumPy y varianza del incremento. [Proceso de Wiener](https://re.public.polimi.it/retrieve/e0c31c09-3f0b-4599-e053-1705fe0aef77/ELS2015_Revised_OSN354.pdf).

## Desequilibrio I/Q

`IQImbalance` conserva I como referencia. La rama Q se multiplica por ganancia de amplitud $g=10^{G_{dB}/20}$ y gira según $e^{j\epsilon}$. Con $c=g e^{j\epsilon}$ y DC complejo $b$, la salida es $y=I+jcQ+b=\alpha x+\beta x^*+b$, donde $\alpha=(1+c)/2$ y $\beta=(1-c)/2$. Un ángulo positivo de Q aporta una componente a −I. El DC usa las unidades de amplitud de entrada. El rechazo de imagen es $20\log_{10}(|\alpha|/|\beta|)$ en dB y se guarda con un estado explícito si alguna de las componentes desaparece. [Desbalance y componente imagen](https://escholarship.org/uc/item/5zn8g5c9).

## Interferencia

`InterferenceSpec` selecciona una fuente tonal, de banda limitada o externa. El cálculo usa el reloj y la ventana de N muestras del registro deseado. La salida conserva el primer índice y las unidades de amplitud. Los componentes usan las mismas coordenadas, escala y ventana.

Cada tono es una exponencial compleja con frecuencia en Hz, amplitud lineal y fase en el primer instante del registro. Para una banda de ancho total B y centro f se rellenan los bins DFT del intervalo semiabierto $[f-B/2,f+B/2)$ con gaussianas complejas, se usa cero en el resto y se transforma por IFFT. La potencia esperada antes de calibración es uno. El modelo de banda se interpreta como una realización sobre la rejilla periódica del registro, con resolución Fs/N. Una banda sin bins o fuera de Nyquist produce un error. Centro cero permite estudiar cocanal. Un centro desplazado permite un interferente en una banda adyacente si los intervalos de la prueba así lo ubican. [Convención DFT](https://numpy.org/doc/stable/reference/routines.fft.html).

Una segunda señal se suma por índices físicos compatibles y vale cero fuera del solapamiento. Si ambas fijan Fs, debe coincidir. Los tiempos iniciales registrados deben ser consistentes con la diferencia de índices. Si ambas declaran unidades de amplitud, deben coincidir. Si ambas registran portadoras, su diferencia se suma al traslado manual en Hz. Se aplica desde el primer instante del registro deseado. La rotación trabaja en banda base discreta y un espectro trasladado puede cruzar Nyquist.

La calibración puede conservar el nivel de la fuente, fijar una potencia media o fijar una SIR objetivo respecto de la señal deseada. La potencia de cada componente es $P=(1/N)\sum_k|x[k]|^2$ e incluye los ceros del solapamiento parcial. La SIR usa $P_s/P_i$, la SNR medida usa $P_s/P_n$ y la SINR usa $P_s/(P_i+P_n)$. Se reporta además $P(i+n)$, que incluye el término cruzado en el registro finito. Se distingue cero, infinito y el caso indeterminado mediante estados serializables. Las relaciones se expresan en dB.

El AWGN opcional reutiliza el motor de Fase 03 con potencia de señal deseada como referencia y subflujo PCG64 independiente de la interferencia de banda. El archivo registra la configuración, ventana, semillas, huellas de los orígenes, potencia de los componentes y huellas de los componentes realizados. La señal, interferencia, ruido disponible e informe se guardan como una sola transacción de proyecto. [SINR](https://web.stanford.edu/class/ee359/doc/WirelessComm_Chp1-7_Feb82020.pdf).

## Propagación a gran escala

`PropagationSpec` aplica una ganancia fija o combina ganancia adicional con pérdida por distancia y sombra. El modelo de espacio libre usa $L(d)=20\log_{10}(4\pi d f_c/c)$ con $d$ en metros, $f_c$ en Hz y $c=299\,792\,458$ m/s. Supone campo lejano entre antenas isotrópicas. Una pérdida básica negativa se rechaza, y una positiva requiere igualmente verificar que se cumplen las condiciones físicas del modelo. Se puede usar la portadora de la señal o declarar una compatible.

Log-distancia usa $L(d)=L_0+10\gamma\log_{10}(d/d_0)$ con exponente positivo y $d\ge d_0$. Si no se da $L_0$, se toma la pérdida de espacio libre a $d_0$. El exponente y el ancla representan el escenario declarado. El modelo de sombra agrega una pérdida gaussiana en dB de media cero y desviación indicada. PCG64 toma un valor por registro, con lo cual la ganancia lineal por sombra sigue una log-normal. Sombra y pérdida por distancia se informan por separado.

La señal se escala por $10^{(G-L-X)/20}$, con $G$ la ganancia adicional, $L$ la pérdida por distancia y $X$ la realización de sombra. Se conservan fase, soporte, reloj y unidades. Esta etapa solo modela escala de amplitud. La demora y la propagación variante se modelan mediante retardo o fading. [UIT-R P.525-5](https://www.itu.int/rec/R-REC-P.525-5-202411-I/en) · [Pérdida por distancia y sombra](https://web.stanford.edu/class/ee359/lectures.html).

## Composición ordenada

`ChannelPipelineSpec` define hasta 128 etapas de los motores de canal. Cada salida es la siguiente entrada y los relojes se recalculan según el modelo. En una cadena vacía, la salida es la propia señal de entrada. Cada etapa conserva su registro, potencia media, reloj, amplitud, parámetros efectivos, huellas, condiciones de uso y realizaciones auxiliares. Las potencias se miden sobre el registro completo de cada etapa, con el soporte que utilice esa operación.

La semilla raíz puede omitirse para usar las semillas originales de cada etapa. Con raíz, `SeedSequence` combina la raíz y la semilla declarada y deriva un subflujo por posición de etapa y por rol. Para interferencia de banda, la banda y el AWGN son roles separados. El resultado de una corrida se reproduce con el mismo orden, entradas, configuración y entorno numérico.

Las interferencias externas se vinculan por nombre antes de ejecutar. El informe conserva huellas de las entradas y vínculos al proyecto. Una sola transacción conserva salida, etapas, componentes e informe. La importación reasigna identificadores manteniendo el orden y las huellas. En ejecución, las señales retenidas consumen una parte del presupuesto disponible para las siguientes etapas. La cancelación es cooperativa en los motores y en la transacción del proyecto.

## Acoplamiento al enlace digital

La cadena recibe la señal conformada por el pulso TX. Si se conserva el AWGN del demostrador, se agrega a la salida de la cadena y su $E_b/N_0$ se refiere a la energía transmitida. Al desactivar el AWGN y usar una cadena vacía, se recupera el enlace ideal de Fase 03. Una cadena vacía con AWGN mantiene el formato y las semillas del control histórico.

La captura de referencia conocida suma los retardos enteros de la primera trayectoria activa y el desplazamiento temporal configurado. Considera también la latencia de los pulsos TX y RX. Cuando se conoce el instante de muestreo pero quedan errores de amplitud o fase, las mediciones describen la recepción con esas imperfecciones. El modo asistido usa el instante y la fase indicados. El modo estimado busca el instante y la fase con el piloto. Los tres métodos quedan identificados en el informe.

Si el receptor entero no puede usar el reloj de llegada, se archiva la señal y la respuesta de los taps nominales aplicada a la tasa recibida. La sincronización queda indisponible y no se calculan BER, SER ni EVM. También queda indisponible la referencia conocida si determina un instante fraccionario o no hay una llegada activa. La simulación de SFO no corrige automáticamente ese error.

El informe de un enlace con cadena incluye parámetros y procedencia de cada etapa. La curva teórica del control AWGN y los intervalos basados en independencia se reservan para configuraciones que satisfacen sus hipótesis. El archivo guarda entrada, etapas, realizaciones, salida final, recepción y métricas disponibles en una sola transacción.

## Campañas y calibración por SINR

El barrido combina ejes numéricos del enlace y de la cadena. Por ejemplo, `channel.2.paths.1.k_linear` indica el factor K del primer camino de la segunda etapa y `channel.1.model.center_hz` el centro de una banda. Los índices empiezan en uno. Una sola referencia de potencia interferente puede variar por etapa. La SINR objetivo fija $P_i+P_n$ a partir de $P_s$ y la relación deseada. Se descuenta la potencia realizada del AWGN antes de escalar la interferencia. Si el propio ruido excede la perturbación admitida, se informa que la calibración resulta inviable.

Cada punto puede repetirse con una réplica numérica independiente. Política común comparte la semilla de cada réplica entre puntos, mientras que la política independiente la deriva por corrida. Ambas políticas generan subflujos para las etapas y conservan la política histórica cuando el barrido legado usa una sola réplica. Se guardan las semillas, las configuraciones efectivas y las huellas de las corridas. Cuando se requiere una señal externa, la copia verificada guardada con el catálogo permite reanudar sin solicitar el archivo original.

El informe por punto calcula medias sobre corridas con métricas disponibles. A partir de tres réplicas válidas con dispersión medida se presenta un intervalo t aproximado al 95 % para la media entre corridas. El cálculo no trata todos los bits de un canal correlacionado como observaciones independientes. Si todas las tasas observadas son cero, la media es cero y se omite el intervalo. El CSV conserva las corridas individuales, su estado de sincronización y las relaciones medidas de las etapas de interferencia.
