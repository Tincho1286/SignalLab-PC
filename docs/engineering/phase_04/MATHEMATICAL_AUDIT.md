# Auditoría matemática de Fase 04

## Multitrayecto

Los casos de regresión comparan un registro complejo con `numpy.convolve`, la respuesta centrada par e impar con `scipy.signal.freqz` y el perfil de dos retardos con cuentas manuales. Dos taps con potencias 4 y 1 a retardos 1 y 5 dan potencia total 5, retardo medio 1,8, dispersión RMS 1,6 muestras y potencia relativa de ISI 1/4 cuando L = 4.

## Protocolo previo para fading independiente

- Usar 32 768 muestras por distribución, una semilla registrada y una entrada constante de amplitud unitaria. Comparar la envolvente con la CDF de SciPy para Rayleigh y Rice, y la fase de Rayleigh con la distribución uniforme en el intervalo de −π a π.
- Exigir distancia máxima entre CDF empírica y teórica menor que 0,015. La cota Dvoretzky–Kiefer–Wolfowitz para una prueba iid de este tamaño da una probabilidad de rechazo bajo el modelo menor que 8 × 10⁻⁷ por distribución. El protocolo de Doppler correlacionado necesita otro criterio.
- Exigir error de potencia media menor al 4 % y error absoluto de la media compleja menor al 3 % de la raíz de la potencia. Comprobar K = 0, LOS dominante, trazas de caminos independientes y salida como suma de copias con sus coeficientes a los índices de llegada.
- Repetir con las mismas semillas y comprobar identidad de realizaciones en el mismo entorno. No comparar por igualdad muestras generadas por bibliotecas o semillas distintas.

[CDF de Rayleigh](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.rayleigh.html) · [CDF de Rice](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.rice.html) · [Modelo estadístico de banda base](https://web.stanford.edu/~dntse/papers/ch1%2B2.pdf)

### Mediciones en Windows

Con potencia 2,7, fase LOS −0,82 rad y semilla 70123, se obtuvieron los resultados de la tabla con las importaciones de Qt bloqueadas.

| Canal | Distancia CDF de envolvente | Distancia CDF de fase | Error relativo de potencia | Error de media dividido por raíz de P |
| --- | ---: | ---: | ---: | ---: |
| Rayleigh | 0,006355 | 0,006371 | 0,001521 | 0,004634 |
| Rician K = 4 | 0,003425 | — | 0,001112 | 0,002072 |

La fase Rician depende de la componente LOS. El protocolo compara CDF de fase uniforme para Rayleigh y media compleja para ambos modelos.

## Protocolo previo para Doppler

- Validar el desplazamiento determinista con exponenciales complejas de fase conocida, en ambas direcciones y con origen distinto de cero. Separar el caso de fase constante, que no requiere Fs.
- Para dispersión Clarke, promediar cuatro realizaciones independientes de 32 768 muestras con $F_s/f_D=64$. Contrastar la autocorrelación normalizada en lags 16, 32 y 64 contra $J_0(2\pi f_D\ell/F_s)$, con error absoluto menor que 0,08.
- Estimar la PSD con Welch y bandas de 2 048 puntos. Exigir más de 99 % de potencia dentro de $[-f_D,f_D]$ con margen de dos bins. Comparar la masa normalizada en $[-f_D/2,f_D/2]$ con la masa teórica 1/3, con tolerancia absoluta 0,04.
- Verificar la coherencia según el primer cruce de 0,5 de la autocorrelación difusa teórica. Con Doppler máximo cero el proceso debe ser fijo durante el registro. Con Doppler muy bajo la variación debe tender a la del caso fijo.

[Correlación y espectro de Clarke](https://web.stanford.edu/~dntse/papers/main.pdf) · [Transformada Zoom FFT](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.ZoomFFT.html)

### Mediciones de Doppler en Windows

Se usaron semillas 2014, 3121, 4919 y 7547, Fs = 4 096 Hz y fD = 64 Hz. Las importaciones de Qt se bloquearon durante el contraste.

| Magnitud | Resultado | Criterio previo |
| --- | ---: | ---: |
| Error absoluto de autocorrelación en lags 16, 32 y 64 | 0,00941 · 0,00859 · 0,00984 | Cada error <0,08 |
| Fracción Welch dentro de ±68 Hz | 0,999996 | >0,99 |
| Fracción Welch dentro de ±32 Hz | 0,344292 | 1/3 ±0,04 |
| Tiempo de coherencia a 0,5 | 0,003782775 s | El primer cruce teórico verifica J₀ = 0,5 |

El ensayo exploratorio de dos caminos sobre 524 288 muestras a Fs = 96 kHz y fD = 250 Hz tardó 0,264 s en esta máquina. La calificación requiere volver a medir latencia, memoria, persistencia y cancelación sobre los perfiles del candidato.
