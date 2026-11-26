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

## Protocolo previo para errores de reloj, fase e I/Q

- Comparar retardos enteros positivos y negativos con un registro desplazado a mano y extensión nula. Para retardos fraccionarios y cambios de tasa, contrastar un tono complejo de frecuencia normalizada $\omega=0,2\pi$ con su valor analítico en los nuevos instantes. Medir error máximo <0,002 en el interior, excluidos 64 puntos de cada borde, con offsets de ±250 ppm y 0,1 ppm. Verificar por separado la longitud, la tasa y el tiempo inicial.
- Para ruido de fase Wiener, estimar la varianza de 65 535 incrementos con semilla fija. Exigir error relativo <3 % frente a $2\pi\Delta\nu/F_s$ y conservar el módulo de cada muestra dentro de 3 × 10⁻¹⁵ en valores unitarios. Comprobar la reproducción de la trayectoria y el caso de linewidth cero.
- Para desequilibrio I/Q, usar un tono ubicado en un bin exacto. Contrastar las componentes del tono, su imagen y DC con proyecciones complejas independientes y la relación de potencias teórica. Verificar identidad e imagen nula sin producir JSON con infinitos.

[Modelo Wiener](https://re.public.polimi.it/retrieve/e0c31c09-3f0b-4599-e053-1705fe0aef77/ELS2015_Revised_OSN354.pdf) · [Modelo de desbalance I/Q](https://escholarship.org/uc/item/5zn8g5c9)

### Mediciones de reloj, fase e I/Q en Windows

Con Qt bloqueado, un tono de ω = 0,2π y un retardo de 0,375 muestras dio errores máximos de 6,54 × 10⁻⁵, 5,94 × 10⁻⁵ y 5,72 × 10⁻⁵ para 250, −250 y 0,1 ppm, respectivamente. En una prueba adicional con Fs de salida igual a la mitad de la original, el acceso a instantes fraccionarios suprimió el tono fuera de banda dentro de la tolerancia de 0,002.

Con Fs = 8 kHz, ancho de línea de 16 Hz y semilla 673, la varianza medida fue 0,0127514 rad² frente a 0,0125664 rad² teóricos. El error relativo fue 1,47 %. La proyección compleja del tono con desbalance de amplitud 1,25, ángulo de 0,23 rad y DC de 0,025 − j0,07 dio 15,90338546 dB de rechazo de imagen, de acuerdo con la relación de coeficientes.

Una ejecución exploratoria de retardo y SFO sobre 524 288 muestras a 96 kHz tardó 2,83 s. El coste de memoria y la respuesta de escritorio se medirán en los perfiles del candidato.

## Protocolo previo para interferencia

- Comparar tonos complejos y su suma con exponenciales analíticas y proyecciones en bins exactos. Verificar el escalado a SIR de 6 dB y preservar el soporte y reloj.
- Generar interferencia cocanal y desplazada con soporte definido en bins. Comparar potencia en banda y fuera de ella mediante DFT independiente y Parseval. Exigir potencia fuera de banda relativa <10⁻²⁶ en los registros de prueba.
- Para una señal externa, calcular a mano los índices de superposición y los ceros del resto del registro. Rechazar incompatibilidades de reloj o unidades registradas.
- Medir por separado P de señal, interferencia y ruido, además de la potencia observada de la suma de los dos últimos. Contrastar SIR y SINR mediante cálculo directo, y comprobar los estados de energía cero sin escribir infinitos en JSON.

[Modelo y convenciones DFT](https://numpy.org/doc/stable/reference/routines.fft.html) · [Definición de SINR](https://web.stanford.edu/class/ee359/doc/WirelessComm_Chp1-7_Feb82020.pdf)

### Mediciones de interferencia en Windows

Con Qt bloqueado se midió un registro de 8 192 muestras a Fs = 4 096 Hz. Se fijó una SIR de 8 dB con banda de 512 Hz centrada en 1 000 Hz y AWGN de SNR nominal de 10 dB. Las semillas fueron 73 para ambas fuentes, derivadas con subflujos separados.

| Magnitud | Resultado |
| --- | ---: |
| Potencia deseada | 4 |
| Potencia interferente | 0,63395728 |
| Potencia del AWGN | 0,40277478 |
| Potencia observada de la suma interferencia + AWGN | 1,04285371 |
| SIR | 8 dB |
| SINR por suma de potencias | 5,86393465 dB |
| Fracción de potencia interferente fuera de los bins configurados | 9,96 × 10⁻³² |
