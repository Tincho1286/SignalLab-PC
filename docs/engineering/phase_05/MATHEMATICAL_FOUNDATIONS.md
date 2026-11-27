# Fundamentos matemáticos · Distribuciones

## Masa, densidad e intervalos

Un valor de PMF describe la probabilidad de un punto. Una PDF es una densidad que se integra sobre los intervalos. Para variables continuas, la probabilidad de un punto es cero incluso cuando su densidad en ese borde diverge. Para una variable entera, la probabilidad cerrada entre a y b es $F(\lfloor b\rfloor)-F(\lceil a\rceil-1)$.

En la cola superior se usan funciones de supervivencia para evitar la resta de una CDF cercana a uno. Para diferencia de log-probabilidades ordenadas, con $\ell_a\ge\ell_b$, se usa $\ell_a+\log[-\operatorname{expm1}(\ell_b-\ell_a)]$. Una probabilidad puede quedar por debajo de la representación de `float64` aunque se conserve su logaritmo. La cola de la envolvente Rician se evalúa mediante $(R/\sigma)^2\sim\chi'^2_2(\nu^2/\sigma^2)$, con $\nu/\sigma$ como parámetro de forma. El caso de relación cero coincide con Rayleigh.

Los cuantiles discretos satisfacen $F(k-1)<q\le F(k)$. Los extremos usan el soporte efectivo cuando la ley se vuelve puntual. El momento solicitado es $E[X^k]$ para orden 0–4. Si las colas impiden la integrabilidad, un momento par no acotado diverge y el momento impar con dos colas divergentes es indefinido. La media indefinida también impide asignar una varianza ordinaria.

## Gaussianas conjuntas y multinomial

Sea $Z=X+iY$ centrada, $C=E[ZZ^H]$ y $P=E[ZZ^T]$. Los bloques de covarianza real son $\operatorname{Cov}(X)=(\Re C+\Re P)/2$, $\operatorname{Cov}(Y)=(\Re C-\Re P)/2$ y $\operatorname{Cov}(X,Y)=(\Im P-\Im C)/2$. En el caso propio $P=0$. La densidad compleja se refiere a las coordenadas reales e imaginarias conjuntas. Una medida singular precisa su subespacio y carece de densidad ordinaria con respecto a todo el espacio.

Para condicionar una gaussiana, se observa parte de $\mu+L\xi$ con $\xi$ normal estándar. La SVD de las filas observadas separa la solución de norma mínima en $\xi$ y el núcleo que conserva incertidumbre. Una observación incompatible con el rango se rechaza. El rango y la condición numérica se determinan a escala de la covarianza. Los resultados informan el rango real efectivo.

Con N ensayos categóricos independientes, el vector de recuentos tiene media $Np$ y covarianza $N(\operatorname{diag}(p)-pp^T)$. Su marginal es binomial. La condicional descuenta los recuentos observados y normaliza las probabilidades restantes. [Contratos](SCIENTIFIC_CONTRACTS.md) · [Protocolo de validación](STATISTICAL_VALIDATION_PROTOCOL.md)
