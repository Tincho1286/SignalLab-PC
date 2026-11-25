# Convenciones matemáticas de SignalLab PC

Contrato de cálculo y de intercambio de resultados para SignalLab PC 2.0.x. La [guía de convenciones de la app](../conventions.md) explica cómo se muestran estos datos.

## Ejes y relojes

| Objeto | Coordenada | Significado |
| --- | --- | --- |
| Registro discreto | `n=n₀+m`, `m=0,…,L−1` | `n₀` es el primer índice de la señal. `m` es la posición dentro del registro. Los índices son enteros y su paso es 1. |
| Registro continuo | `t=t₀+m·Δt`, en s | El modelo declara si hay interpolación, retención o cuadratura. Los datos son muestras ordinarias. Los impulsos ideales se guardan por posición y peso. |
| Reloj de una secuencia | `t(n)=time_start_s+(n−n₀)/Fs` | `Fs` está en muestras/s. Se puede conocer `Fs` sin conocer el instante de la primera muestra. No se inventa un origen físico. |
| Frecuencia digital | `ω` en rad/muestra, `k` en bins | Para una DFT de largo `N`, `ωₖ=2πk/N`. La representación centrada elige un conjunto de `N` bins en `−π ≤ ω < π`. |
| Frecuencia continua | `Ω` en rad/s, `f` en Hz | `Ω=2πf`. Cuando se conoce `Fs`, la correspondencia digital es `ω=Ω/Fs=2πf/Fs`. La frecuencia digital se interpreta módulo `2π`. |

El registro discreto finito se extiende con ceros cuando el cálculo así lo declara. Una serie discreta o convolución circular usa por separado un modelo periódico. En reconstrucción, el alcance del resultado depende del reloj, la rejilla y el método de interpolación. En muestreo, usar el criterio de Nyquist exige una hipótesis de banda limitada.

## Transformadas y normalización

| Cálculo | Convención |
| --- | --- |
| DFT por posiciones | `Xᵣ[k]=Σₘ v[m]·exp(−j2πkm/N)`, con `m=0,…,N−1`. Se agregan ceros o se trunca antes de transformar cuando se pide un `N` distinto de `L`. |
| DFT por índices | `Xₙ[k]=Σₘ v[m]·exp(−j2πk(n₀+m)/N)`. Equivale a `Xᵣ[k]·exp(−j2πkn₀/N)`. Coincide con la DTFT del mismo registro en `ωₖ`. |
| IDFT | Signo positivo y factor `1/N`. Para `Xₙ`, se recupera `v[m]` en `n₀+m` y luego se aplica el origen elegido para el eje de salida. Para `Xᵣ`, se evalúa directamente en `m`. |
| DTFT | `X(ω)=Σₙ x[n]·exp(−jωn)`. La inversa ordinaria integra un período con factor `1/(2π)` y exponente `+jωn`. Las transformadas distribucionales requieren una interpretación explícita. |
| Fourier continua | `X(Ω)=∫ x(t)·exp(−jΩt) dt`. La inversa angular usa signo positivo y factor `1/(2π)`. Una evaluación numérica en intervalo finito aproxima la integral según la rejilla y el método. |
| Series de Fourier | El coeficiente directo se normaliza por `1/T` en tiempo continuo y por `1/N` en discreto. La síntesis usa signo positivo y suma los coeficientes según sus índices armónicos. |
| Laplace | `X(s)=∫ x(t)·exp(−st) dt`. Se declara si la interpretación es bilateral o unilateral. Para las ecuaciones que conservan el estado anterior al origen, se usan datos en `0−`. |
| Z | `X(z)=Σₙ x[n]·z^(−n)`. La expresión y su ROC forman el resultado bilateral. Los términos con avances y retardos conservan sus potencias. |

El signo de correlación discreta es `rₓₕ[ℓ]=Σₙ x[n]·conj(h[n−ℓ])`. FFT designa el algoritmo. El número de puntos, el orden de los bins y su unidad son decisiones independientes de la referencia de fase.

### Intercambio de fase en DFT

El cálculo nuevo desde **DFT → Transformada directa** usa **Índices de la señal (n)** por defecto. El usuario puede elegir **Primera muestra del registro (m=0)**. Para mantener los resultados de scripts existentes, `operations.dft(x)` sigue usando la primera muestra como referencia por defecto. La opción se expresa con `phase_reference='sample_indices'` o `phase_reference='record_offset'`.

Los resultados conservan `dft_phase_reference`, el índice inicial y la cantidad `N`. Guardar, reutilizar o abrir un archivo JSON/CSV conserva esos campos. Un resultado antiguo de DFT directa sin la marca se lee con referencia a `m=0`. Un documento de DFT de una sesión histórica también recupera `m=0` para recalcular con la misma convención. Una DFT enventanada angular histórica ya usaba los índices `n`. Sus coeficientes no centrados siguen disponibles para invertirla.

La DFT inversa necesita los bins completos para un espectro centrado o para una DFT con fase en `n`. Sin una marca de origen de fase, una lista manual se interpreta como `Xᵣ` en orden `k=0,…,N−1`. Conservar las muestras y cambiar el eje de salida a cero es una relabelización. La corrección de fase se aplica por separado y en ambos modos de salida.

Ejemplo de control. `x[3]=1`, `x[4]=2` y las dos muestras siguientes son cero. En `k=1` y `N=4`, la DFT por posiciones da `1−2j`. La fase por índices y la DTFT evaluada en `π/2` dan `2+j`. El módulo es `√5` en ambos casos. Las pruebas calculan la suma directamente y reducen los productos de índices módulo `N` antes de evaluar el exponente.

## Representación compleja y validez

Las muestras se guardan como complejos de doble precisión. Al exportarlas se conservan partes real e imaginaria. El módulo y el ángulo son representaciones derivadas. Donde el módulo vale cero, el ángulo es indefinido. La fase principal puede saltar `2π`; una fase desenrollada se interpreta por tramos continuos válidos. El retardo de grupo es la derivada negativa de la fase respecto de la frecuencia angular y sus unidades son muestras para `ω` o segundos para `Ω`.

La DFT de un registro conserva energía por Parseval con factor `1/N` del lado espectral. Densidad espectral de potencia y densidad de energía representan cantidades diferentes. Las unidades del eje deben acompañar el resultado para interpretar una densidad integrada. Una salida numérica finita no demuestra por sí sola una propiedad sobre todo el eje.

Una respuesta racional de Laplace o Z se lee como transformada de Fourier cuando su ROC contiene el eje imaginario o el círculo unitario correspondiente. La estabilidad interna de una realización se verifica sobre sus modos. La estabilidad BIBO corresponde a la transferencia y a su ROC. Conservar las condiciones simbólicas evita tratar singularidades o valores excluidos como puntos válidos por redondeo.
