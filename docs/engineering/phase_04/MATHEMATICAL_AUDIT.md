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
