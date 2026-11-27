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
