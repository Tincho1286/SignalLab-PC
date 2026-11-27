# Fundamentos matemáticos · Probabilidad y estadística

## Masa, densidad e intervalos

Un valor de PMF describe la probabilidad de un punto. Una PDF es una densidad que se integra sobre los intervalos. Para variables continuas, la probabilidad de un punto es cero incluso cuando su densidad en ese borde diverge. Para una variable entera, la probabilidad cerrada entre a y b es $F(\lfloor b\rfloor)-F(\lceil a\rceil-1)$.

En la cola superior se usan funciones de supervivencia para evitar la resta de una CDF cercana a uno. Para diferencia de log-probabilidades ordenadas, con $\ell_a\ge\ell_b$, se usa $\ell_a+\log[-\operatorname{expm1}(\ell_b-\ell_a)]$. Una probabilidad puede quedar por debajo de la representación de `float64` aunque se conserve su logaritmo. La cola de la envolvente Rician se evalúa mediante $(R/\sigma)^2\sim\chi'^2_2(\nu^2/\sigma^2)$, con $\nu/\sigma$ como parámetro de forma. El caso de relación cero coincide con Rayleigh.

Los cuantiles discretos satisfacen $F(k-1)<q\le F(k)$. Los extremos usan el soporte efectivo cuando la ley se vuelve puntual. El momento solicitado es $E[X^k]$ para orden 0–4. Si las colas impiden la integrabilidad, un momento par no acotado diverge y el momento impar con dos colas divergentes es indefinido. La media indefinida también impide asignar una varianza ordinaria.

## Gaussianas conjuntas y multinomial

Sea $Z=X+iY$ centrada, $C=E[ZZ^H]$ y $P=E[ZZ^T]$. Los bloques de covarianza real son $\operatorname{Cov}(X)=(\Re C+\Re P)/2$, $\operatorname{Cov}(Y)=(\Re C-\Re P)/2$ y $\operatorname{Cov}(X,Y)=(\Im P-\Im C)/2$. En el caso propio $P=0$. La densidad compleja se refiere a las coordenadas reales e imaginarias conjuntas. Una medida singular precisa su subespacio y carece de densidad ordinaria con respecto a todo el espacio.

Para condicionar una gaussiana, se observa parte de $\mu+L\xi$ con $\xi$ normal estándar. La SVD de las filas observadas separa la solución de norma mínima en $\xi$ y el núcleo que conserva incertidumbre. Una observación incompatible con el rango se rechaza. El rango y la condición numérica se determinan a escala de la covarianza. Los resultados informan el rango real efectivo.

Con N ensayos categóricos independientes, el vector de recuentos tiene media $Np$ y covarianza $N(\operatorname{diag}(p)-pp^T)$. Su marginal es binomial. La condicional descuenta los recuentos observados y normaliza las probabilidades restantes. [Contratos](SCIENTIFIC_CONTRACTS.md) · [Protocolo de validación](STATISTICAL_VALIDATION_PROTOCOL.md)

## Inferencia y ajuste

Para observaciones IID normales, el contraste de media usa $(\bar x-\mu_0)/e$ con $e=\sigma/\sqrt{N}$ si la desviación es conocida y $e=s/\sqrt{N}$ si se estima con divisor $N-1$. En dos muestras independientes, Welch suma las varianzas de ambas medias y aproxima los grados de libertad. Para contrastar una varianza normal, $(N-1)s^2/\sigma_0^2$ sigue una χ² con $N-1$ grados de libertad. Para el cociente de varianzas de dos poblaciones normales independientes se usa F con los grados de cada muestra. En todos los casos el intervalo bilateral se obtiene con un cuantil de cada cola. [Intervalo para una varianza normal](https://www.itl.nist.gov/div898/handbook/prc/section2/prc231.htm)

El contraste binomial cuenta éxitos en observaciones 0 o 1 y el intervalo de Clopper–Pearson invierte las dos colas del recuento. En una prueba bilateral, el valor p binomial por orden de probabilidad y el intervalo central pueden dar decisiones distintas cerca del umbral. El intervalo estima una proporción y no exige simetría alrededor de la observación.

En KS se comparan la CDF empírica y una CDF continua, con parámetros fijados antes de tomar la muestra. En normalidad con parámetros desconocidos, Anderson–Darling y Shapiro–Wilk usan calibraciones adecuadas a ese supuesto. El valor p interpolado de Anderson–Darling se informa como cota en los extremos de su tabla. Si esa cota es insuficiente para compararla con α, la decisión queda indeterminada. El valor p de Shapiro–Wilk tiene exactitud limitada para más de 5000 observaciones. Ljung–Box aplica una aproximación χ² a la suma ponderada de autocorrelaciones. La cantidad de retardos y los parámetros estimados afectan sus grados de libertad. [Anderson–Darling](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.anderson.html) · [Shapiro–Wilk](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.shapiro.html)

La máxima verosimilitud estima parámetros que maximizan el producto de las densidades o masas de las observaciones. El método de los momentos iguala momentos muestrales y del modelo. Una uniforme ajustada por momentos puede dejar observaciones fuera de su soporte, en cuyo caso su verosimilitud es cero. En una comparación contra una distribución ajustada con la misma muestra, el valor p del KS de parámetros fijos queda fuera de su calibración. [Ajuste y calibración con parámetros libres](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.goodness_of_fit.html)

Con observaciones IID se pueden pedir intervalos bilaterales para parámetros ajustados. La normal usa los pivotes t y χ². La lognormal los aplica a los logaritmos. Para escala exponencial y Rayleigh se usa la distribución χ² de la suma de valores o cuadrados, respectivamente, con ubicación conocida en cero. La tasa Poisson usa el intervalo de Garwood. El intervalo de la proporción binomial agrega recuentos cuando todos representan el mismo número conocido de ensayos. Los intervalos de varios parámetros se informan por parámetro, con confianza marginal.

## Trayectorias y transiciones

La caminata gaussiana especifica deriva y desviación por muestra. Wiener define deriva $\mu$ y difusión $\sigma$ por tiempo, con incremento de media $\mu\Delta t$ y varianza $\sigma^2\Delta t$. Poisson acumula incrementos independientes de media $\lambda\Delta t$. Con un estado inicial fijo, la covarianza de cualquiera de los tres modelos entre dos posiciones es la varianza al instante menor. Sus trayectorias suelen ser no estacionarias aunque los incrementos sean estacionarios.

Ornstein–Uhlenbeck usa $\phi=e^{-\theta\Delta t}$ y la transición condicional de media $\phi x+(1-\phi)m$ y varianza $\sigma^2(1-\phi^2)/(2\theta)$. Con inicio estacionario, la varianza constante es $\sigma^2/(2\theta)$. Con inicio fijo, la varianza parte de cero. En ambos casos, la covarianza entre $t_1\le t_2$ es $\operatorname{Var}(X_{t_1})e^{-\theta(t_2-t_1)}$. El cálculo usa `expm1` para conservar la deriva y la varianza con pasos muy pequeños. [Transición exacta](https://doi.org/10.1103/PhysRevE.54.2084)

En el telegráfico, dos tasas fijan la ocupación estacionaria y la rapidez de mezcla. La probabilidad de pasar de bajo a alto en $t$ es $\lambda_+ (1-e^{-(\lambda_++\lambda_-)t})/(\lambda_++\lambda_-)$. El salto opuesto se obtiene intercambiando ambas tasas. La muestra solo registra el estado en cada instante y admite múltiples saltos entre muestras. En Markov discreto la transición de $k$ pasos es $P^k$ y una distribución estacionaria satisface $\pi P=\pi$. El informe solo automatiza el inicio en equilibrio si puede determinar una distribución estacionaria única. La existencia de esa distribución no implica mezcla desde un estado dado, por ejemplo en una cadena periódica.

## Modelos de ruido

El blanco gaussiano propio reparte la potencia entre componentes real e imaginaria independientes. El impulsivo usa una mezcla centrada con desviaciones de fondo e impulso. Su varianza es $(1-p)\sigma_0^2+p\sigma_1^2$. Como cada muestra usa un sorteo separado, la mezcla sigue siendo blanca. El color describe la distribución de potencia por frecuencia y la distribución de amplitud describe los valores de las muestras.

La síntesis por FFT usa una PSD bilateral por Hz. Se multiplica el espectro del ruido blanco unitario por $\sqrt{F_s S(f_k)}$ y se aplica la inversa. De Parseval se obtiene la varianza en esperanza $\Delta f\sum_k S(f_k)$ con $\Delta f=F_s/N$. Una densidad plana $\sigma^2/F_s$ recupera ruido blanco de varianza $\sigma^2$. Rosa, marrón, azul y violeta usan potencias de frecuencia de orden −1, −2, 1 y 2 dentro de la banda indicada. Para una entrada por pares, la aplicación interpola linealmente entre puntos y asigna cero fuera del intervalo. Con N par se conserva un único bin de Nyquist en el extremo negativo. Las realizaciones por FFT tienen covarianza circular en una grilla finita. [Escalas espectrales y Parseval](https://docs.scipy.org/doc/scipy/tutorial/signal.html#spectral-analysis)

El ruido por FIR se genera filtrando un ruido blanco cuya prehistoria es aleatoria e independiente. Para un filtro de coeficientes $h_j$, la varianza de salida es $\sigma^2\sum_j|h_j|^2$. Su PSD teórica es $\sigma^2|H(e^{j2\pi f/F_s})|^2/F_s$. Una grilla de PSD gruesa puede integrar con error la potencia del FIR, cuya varianza se calcula en el dominio temporal.

## Correlación, covarianza y conjunto

La estimación temporal recorta los registros a la intersección de índices observados. Conserva la convención $R_{xy}[k]=\sum_n x[n+k]\overline{y[n]}/d_k$. El divisor $d_k$ puede ser N o N−|k|. Para covarianza se restan las medias de la intersección. Para normalizar se divide por la raíz del producto de las potencias o varianzas de ese intervalo. Los estimadores con divisor variable pueden superar uno en módulo al normalizarse de esta forma. La covarianza con media estimada puede conservar sesgo al dividir por pares disponibles.

La matriz toma un vector complejo de canales simultáneos por observación. Con $u=x-\hat\mu$, agrega $uu^H$ para covarianza y $uu^T$ para pseudocovarianza. El divisor N−1 corrige el sesgo de la estimación con observaciones IID. N describe la dispersión observada. La matriz de correlación escala por las desviaciones de cada canal. Si un canal es constante, su coeficiente normalizado queda indefinido. Las mediciones de un único registro suelen tener dependencia temporal, incluso cuando el modelo es estacionario.

Para momentos de conjunto se calcula sobre múltiples trayectorias independientes en posiciones fijas. Las trayectorias deben coincidir en eje y unidades. El promedio y la varianza del incremento usan el valor en la segunda posición menos el de la primera para cada trayectoria. Si hay una referencia de proceso registrada en común se presenta como propiedad del modelo. El conjunto finito mantiene incertidumbre muestral.

## Identificación autorregresiva

Burg minimiza la suma de los cuadrados de los errores hacia adelante y atrás en cada nivel. Si los pares de error son $f_i,b_i$, el coeficiente de reflexión del denominador es $\kappa=-2\sum_i f_i b_i/\sum_i (f_i^2+b_i^2)$. La actualización combina el polinomio anterior con su reverso desplazado y multiplica la varianza de innovación por $1-\kappa^2$. En el modelo $x_n=c+\sum_j\phi_j x_{n-j}+e_n$, los signos de $\phi$ son los opuestos a los del denominador. Una reflexión unitaria indica que el registro no identifica un modelo causal estable de ese orden. [Derivación de Burg](https://sep.sites.stanford.edu/publications/theses/maximum-entropy-spectral-analysis-sep-6-1975)

La PACF al retardo k es el último coeficiente del predictor lineal que usa los k retardos anteriores. Se calcula con la recursión de Levinson sobre covarianzas a partir de cero. Para una varianza nula o una sucesión incompatible con covarianza positiva definida, se conserva el resto del análisis sin asignar una PACF ficticia. Las curvas de residuos usan el tramo de entrenamiento. El rango temporal de validación queda fuera del ajuste.

## Verosimilitud condicional y ARIMA

Sea $y_n=\Delta^d x_n$. La estimación calcula innovaciones aplicando $A(z^{-1})/B(z^{-1})$ a $y_n-\mu$ con el filtro inicialmente en reposo. Para coeficientes fijos, estima $\mu$ por regresión en ese mismo filtro. Optimiza la suma de cuadrados de las innovaciones del soporte elegido y estima su varianza con divisor igual a su cantidad. Esta es una verosimilitud gaussiana condicional a la inicialización y al tramo inicial excluido. El ajuste parte de coeficientes de reflexión para favorecer un núcleo estable e invertible. Se vuelve a comprobar el módulo de polos y ceros en los coeficientes calculados. Rango insuficiente, raíces próximas a cancelarse y residuos compatibles con redondeo impiden asignar criterios de selección.

AIC, AICc y BIC cuentan p coeficientes autorregresivos, q coeficientes de media móvil, una media y una varianza. La comparación usa el mismo d y soporte de ajuste para cada par. El pronóstico actualiza el estado condicionado a las observaciones hasta el último valor, incluidos los antecedentes de la reserva, con parámetros fijos. Para volver a niveles suma las predicciones a las últimas diferencias observadas. La varianza predictiva en el horizonte h suma $\sigma_e^2\sum_{j=0}^{h-1}\psi_j^2$, con $\psi_j$ de la respuesta de $B/[A(1-z^{-1})^d]$. El intervalo es marginal por horizonte y condicionado a los parámetros estimados.

## Bartlett y cobertura de ruido blanco

Bartlett divide el registro en bloques rectangulares disjuntos de M muestras. Promedia $|\mathrm{DFT}(x_b)|^2/(F_s M)$ de los bloques completos. La integral discreta de la densidad bilateral recupera la potencia media de las muestras utilizadas. En una densidad unilateral de señal real se suman los pares de frecuencias, y DC y Nyquist conservan su potencia. [Escalas espectrales](https://docs.scipy.org/doc/scipy/tutorial/signal.html#spectral-analysis)

Para L bloques independientes de ruido gaussiano blanco de media cero, $\nu\widehat S/S$ sigue χ² con $\nu=2L$ en los bins complejos. En señales reales, DC y Nyquist par tienen solo una coordenada real y $\nu=L$. Si se retiró la media del bloque, el intervalo en DC se omite. La banda del gráfico representa la cobertura marginal por frecuencia. El solape o una ventana no rectangular requieren otra calibración.

## Espectro cruzado y coherencia

La densidad cruzada bilateral usa el promedio de $X_b(f)\overline{Y_b(f)}$ dividido por $F_s\sum_n w_n^2$. Se aplican la misma ventana, segmentos y normalización a las densidades individuales. Bajo esta convención, un retardo de x respecto de y introduce fase negativa en la componente de frecuencia positiva. La densidad cruzada compleja conserva su fase y unidades de amplitud de x por amplitud de y por Hz.

La coherencia de magnitud al cuadrado es $|S_{xy}|^2/(S_{xx}S_{yy})$. Se calcula sobre los productos ya promediados. Para un solo bloque queda indefinida porque el cociente sería uno en cualquier bin de potencia no nula. Con dos o más bloques sigue sin definirse en los bins de potencia nula. El solape puede reducir la cantidad de observaciones independientes. El cálculo conserva coherencia y espectro cruzado representable cuando las unidades de uno de los canales llevan su propio PSD fuera del rango numérico.

## Estimación espectral avanzada

Blackman–Tukey calcula la DFT de la autocovarianza hermítica con divisor N, ponderada por $1-|k|/(L+1)$ en los retardos $-L\le k\le L$. La ventana triangular preserva la positividad de la estimación. La división por $F_s$ produce densidad por Hz. Para procesos de media desconocida, retirar la media hace que este cálculo describa las fluctuaciones. [Blackman y Tukey](https://onlinelibrary.wiley.com/doi/abs/10.1002/j.1538-7305.1958.tb03874.x)

Multitaper promedia los periodogramas de las primeras K ventanas DPSS con pesos iguales. Cada periodograma usa $F_s\sum_n w_k[n]^2$ como denominador. NW controla la concentración en una banda y los autovalores informados cuantifican la concentración de cada ventana. La ventana con menor concentración puede aumentar la fuga espectral. [Thomson](https://doi.org/10.1109/PROC.1982.12433)

La PSD autorregresiva evalúa $\sigma_e^2/(F_s|A(e^{-j\omega})|^2)$ con los parámetros de Burg. Representa el proceso ajustado y omite la línea espectral de una media no nula. Lomb–Scargle trabaja sobre tiempos irregulares con una regresión de seno, coseno y término constante. Su normalización es la reducción de la suma de cuadrados frente al modelo constante, dividida por la suma de cuadrados del modelo constante. El resultado es adimensional y depende de la rejilla de frecuencias elegida. [Modelo de Lomb–Scargle](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.lombscargle.html)

## Estimación gaussiana lineal

Sea $y=A\theta+v$ con $v$ gaussiano real, centrado y de covarianza conocida $R=L_RL_R^T\succ0$. La log-verosimilitud usa la norma cuadrática de $L_R^{-1}(y-A\theta)$ y el logaritmo del determinante de $R$. La SVD de $L_R^{-1}A$ permite calcular ML y la cota de Cramér–Rao cuando todas las columnas son identificables. La información de Fisher es $(L_R^{-1}A)^T(L_R^{-1}A)$. En este modelo, ML de rango completo es insesgado y alcanza la cota. [Modelo gaussiano lineal](https://ocw.mit.edu/courses/18-655-mathematical-statistics-spring-2016/b36cbb44af02cddb9dc42d92b767c462_MIT18_655S16_LecNote19.pdf)

Con media previa $m$ y covarianza $P=L_PL_P^T\succ0$, el posterior es gaussiano. Las raíces de covarianza en coordenadas normalizadas se contraen con los factores $1/\sqrt{1+s_i^2}$ de la SVD de $L_R^{-1}AL_P$. Las direcciones no observadas conservan factor uno. La media coincide con MAP, MMSE y LMMSE. La traza de la covarianza es el MSE integrado bajo el modelo previo. Si se fija un parámetro de referencia, también se informa el MSE de mediciones repetidas en ese punto. [Estimación MMSE y LMMSE](https://ocw.mit.edu/courses/6-011-introduction-to-communication-control-and-signal-processing-spring-2010/resources/mit6_011s10_chap08/)

## Wiener FIR causal

Se estima $d[n]$ mediante $\sum_{k=0}^{L-1}h_k x[n-k]$. Para un modelo conjuntamente estacionario, el error ortogonal a todas las entradas determina $Rh=p$, con $R_{ij}=R_{xx}[i-j]$ y $p_i=E[d[n]\overline{x[n-i]}]$. En rango deficiente se usa la solución de norma mínima y se verifica que p pertenezca al rango de R. El MSE mínimo es $E|d[n]|^2-p^H h$. Para datos centrados, las medias se usan aparte para obtener el término constante. [Wiener FIR y ortogonalidad](https://ocw.mit.edu/courses/6-011-introduction-to-communication-control-and-signal-processing-spring-2010/f135b328c7448bf21c4939ea9ff8f8fb_MIT6_011S10_chap11.pdf)

El estimador empírico resuelve por SVD la regresión sobre ventanas completas, sin formar las ecuaciones normales. El historial de la señal observada sigue disponible al empezar la validación. Los objetivos reservados se usan para evaluar los errores después de entrenar. El estimador con constante es afín, con el offset fuera de la transferencia FIR.

## Kalman lineal discreto

El cálculo empieza con la distribución previa del estado en el primer instante registrado. Aplica $x[n+1]=Ax[n]+Bu[n]+w[n]$ y $y[n]=Cx[n]+Du[n]+v[n]$. Los ruidos del proceso y la medición son blancos, de media cero y mutuamente independientes. En el caso complejo se suponen propios. Cuando falta parte de una observación, la corrección usa las filas disponibles de C y la submatriz de varianzas y covarianzas de esos sensores. Si faltan todas, se conserva la predicción. [Kalman](https://cs-www.cs.yale.edu/homes/yry/readings/general/Kalman1960.pdf)

Para la predicción, una raíz de la covarianza satisface $P=LL^H$. Se propagan los factores $AL$ y $Q^{1/2}$ y se compactan por QR. Para corregir se hace una SVD de $[CL, R^{1/2}]$ usando los sensores disponibles. Las direcciones observables determinan la ganancia y el espacio nulo determina la raíz de la covarianza corregida. Así se evita la resta de dos covarianzas casi iguales y cada matriz reconstruida es un producto de Gram. Las pruebas comparan esta actualización con Joseph y con el condicionamiento conjunto de las observaciones anteriores. Las covarianzas de entrada y las innovaciones usan tolerancias relativas a su escala para detectar rango numérico. Una medición que contradice una restricción determinista produce un diagnóstico. [Estabilidad de las formulaciones por raíces](https://ntrs.nasa.gov/citations/19890058774)

## Filtrado adaptativo FIR

Para una fila de entrada $u_n$ que contiene las muestras retardadas y coeficientes $h_n$, la predicción previa es $\hat d_n=u_n h_n$ y el error es $e_n=d_n-\hat d_n$. LMS actualiza $h_{n+1}=h_n+\mu u_n^H e_n$. NLMS divide la corrección por $\|u_n\|^2+\varepsilon$. Un paso que funciona con una entrada puede ser demasiado grande al amplificarla. Bajo el modelo usual de independencia entre el error de coeficientes y la fila de entrada, la estabilidad media de LMS requiere $0<\mu<2/\lambda_{\max}(E[u^H u])$. La excitación suficiente y un paso de NLMS entre cero y dos favorecen la convergencia. La estabilidad media, el error cuadrático y la convergencia en un registro tienen criterios distintos. [Análisis de LMS](https://isl.stanford.edu/~widrow/papers/j1976stationaryand.pdf)

Después de procesar k filas, RLS minimiza $\sum_{n=0}^{k-1}\lambda^{k-1-n}|d_n-u_n h|^2+\gamma\lambda^k\|h\|^2$. Las rotaciones de Givens actualizan los factores QR y preservan el problema de mínimos cuadrados sin formar una inversa de covarianza. La regularización inicial se atenúa con la misma regla de olvido. El rango numérico puede quedar comprometido si el modelo recibe poca excitación y esa regularización se vuelve insignificante. [RLS en forma de raíz](https://ieeexplore.ieee.org/document/295229/)

En identificación, el objetivo es la salida observada. En predicción, solo se permiten muestras anteriores. En cancelación, el FIR aprende la parte del registro contaminado explicada por la referencia de ruido. Si la referencia también está correlacionada con la señal útil, una parte de esa señal se puede atenuar. Las comparaciones mantienen la misma ventana, inicialización en cero y reserva final. [Cancelación adaptativa](https://isl-www.stanford.edu/~widrow/papers/j1975adaptivenoise.pdf)
