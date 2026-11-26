# Convenciones matemáticas

## Constelaciones y etiquetas

En PSK la posición geométrica $i$ avanza en sentido antihorario a partir de la rotación $\phi$, medida en radianes. El punto es $A\exp(j(\phi+2\pi i/M))$ y su etiqueta natural es $i$. El mapeo Gray asigna a la posición $i$ la etiqueta binaria reflejada, incluido el cierre entre la última posición y la primera. QPSK del demostrador usa $\phi=\pi/4$ y energía media unitaria. Los conjuntos de ejes de QAM son $2i-(L-1)$, con $L=\sqrt M$. El etiquetado concatena las palabras de I y Q, Gray por eje si se selecciona. La rotación se aplica a la grilla completa.

La energía media de PSK antes de normalizar es $A^2$. La QAM con separación entre vecinos igual a 2 tiene energía media $2(M-1)/3$, por la suma de cuadrados de los dos ejes. La normalización unitaria divide los puntos por la raíz de su energía media. La decisión dura minimiza la distancia euclídea en el plano complejo. Las fronteras se resuelven mediante el mismo orden de desempate en todas las interfaces. [Geometría QAM](https://komm.dev/ref/QAMConstellation/) · [Decisiones de constelación](https://wiki.gnuradio.org/index.php/Constellation_Object)

## Pulsos y retardo

El tiempo adimensional es $u=t/T_s$ y $\operatorname{sinc}(u)=\sin(\pi u)/(\pi u)$. Para $0<\beta\leq1$, el pulso RC de pico uno es

$$
h_{\mathrm{RC}}(u)=\operatorname{sinc}(u)\frac{\cos(\pi\beta u)}{1-(2\beta u)^2}.
$$

En $u=\pm1/(2\beta)$ vale $(\pi/4)\operatorname{sinc}(1/(2\beta))$. El pulso RRC continuo, antes de la normalización discreta, es

$$
h_{\mathrm{RRC}}(u)=\frac{\sin(\pi u(1-\beta))+4\beta u\cos(\pi u(1+\beta))}
{\pi u(1-(4\beta u)^2)}.
$$

En cero vale $1+\beta(4/\pi-1)$. En $u=\pm1/(4\beta)$ vale
$\beta/\sqrt{2}\,[(1+2/\pi)\sin(\pi/(4\beta))+(1-2/\pi)\cos(\pi/(4\beta))]$.
Con $\beta=0$ ambos pulsos se reducen a $\operatorname{sinc}(u)$. El espectro de RRC se verifica mediante la raíz del espectro de RC y su integral inversa. [RRC](https://komm.dev/ref/RootRaisedCosinePulse/) · [Pulso y filtrado adaptado](https://pysdr.org/content/pulse_shaping)

Con longitud $N$ y simetría, el retardo del FIR causal es $(N-1)/2$ muestras. RC y RRC toman $N=\text{span}\cdot L+1$ con separación $1/L$, incluidos los extremos. El rectángulo toma $N=\text{span}\cdot L$ y muestrea dentro de la duración del pulso. Los FIR de longitud par tienen centro entre muestras. La normalización por pico usa la amplitud teórica en ese centro y la normalización por energía usa los coeficientes discretos. El filtro adaptado es el conjugado del pulso de transmisión invertido. Su ganancia de pico es la energía discreta $E_p=\sum_n|h[n]|^2$ y el par de filtros tiene retardo entero $N-1$. Se declara esa escala antes de decidir o medir EVM. El truncamiento se estudia con la autocorrelación en múltiplos de muestras/símbolo y con la cola conservada en el FIR de longitud completa.

## AWGN y mediciones

Para símbolos equiprobables, $E_s=E_{\mathrm{constelación}}E_p$ en unidades discretas. Con $k=\log_2 M$, la referencia nominal sin codificación es $E_b=E_s/k$. Para datos ya muestreados, el modo SNR por muestra usa la potencia medida o declarada $P_s$ en el intervalo definido, y $P_n=P_s\,10^{-\mathrm{SNR_{dB}}/10}$.

En modo $E_s/N_0$ se obtiene $N_0=E_s10^{-(E_s/N_0)_{\mathrm{dB}}/10}$. En modo $E_b/N_0$, $N_0=(E_s/k)10^{-(E_b/N_0)_{\mathrm{dB}}/10}$. Para AWGN complejo circular, $P_n=N_0$ y cada componente tiene varianza $N_0/2$. Para un canal real, $P_n=N_0/2$ y las muestras permanecen reales. La relación $P_s=E_s/L_{\mathrm{sps}}$ requiere el promedio estacionario con símbolos centrados e independientes. Los bordes de un registro finito pueden apartarse de esa relación. Se registran por separado la potencia finita medida y la normalización del experimento. [Relaciones SNR, Es/N0 y Eb/N0](https://www.mathworks.com/help/comm/ref/comm.awgnchannel-system-object.html)

Después de alinear, BER y SER son errores divididos por los respectivos datos útiles. Se excluyen relleno y transitorios según el alcance indicado en el resultado. Para referencia $s$ y observación compensada $r$, la EVM se mide como

$$
\mathrm{EVM}_{\mathrm{RMS}}=\sqrt{\frac{\sum_i|r_i-s_i|^2}{\sum_i|s_i|^2}}.
$$

Su porcentaje es $100\,\mathrm{EVM}_{\mathrm{RMS}}$ y sus dB se calculan como $20\log_{10}\mathrm{EVM}_{\mathrm{RMS}}$ para un valor positivo. Se guarda la referencia y la ganancia aplicada.

En AWGN ideal coherente, BER BPSK y BER QPSK Gray son $Q(\sqrt{2E_b/N_0})$. SER QPSK es $2p-p^2$ con ese $p$. Para QAM cuadrada equiprobable y detección coherente, $q=Q(\sqrt{3E_s/((M-1)N_0)})$ y $\mathrm{SER}=1-[1-2(1-1/\sqrt M)q]^2$. Una referencia aproximada de BER Gray a SNR moderada o alta es $4(1-1/\sqrt M)q/k$, dominada por vecinos. Los resultados finitos de RRC truncado y sincronización mantienen sus condiciones de ensayo. [Fórmulas de referencia](https://www.mathworks.com/help/comm/ug/analytical-expressions-used-in-berawgn-function-and-bit-error-rate-analysis-app.html)
