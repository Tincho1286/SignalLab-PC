# Señales Aleatorias: cobertura y próximas herramientas

Estado: 1.1.0, 29/10/2026. Referencia: Programa Señales Aleatorias.pdf, contenidos analíticos de las páginas 5–9. Se consultaron las páginas escaneadas del documento original. Esta tabla distingue herramientas operativas de temas todavía pendientes; no declara cobertura completa de la materia.

| Eje del programa | Herramientas disponibles | Alcance pendiente |
|---|---|---|
| I. Procesos y conceptos básicos | Estadísticas de un registro, auto/correlación cruzada y covarianza; curvas de un modelo estacionario AR/MA/ARMA. | Promedios de conjunto y distribuciones conjuntas; herramientas para explorar no estacionariedad y ergodicidad sin inferirlas de un único registro. |
| II. Sistemas lineales con entradas aleatorias | Modelo discreto real, causal y estable excitado por ruido blanco gaussiano; media, varianza, autocovarianza, autocorrelación y PSD teóricas. H(z) reutilizable en análisis de sistemas. | Entradas de espectro arbitrario y tratamiento estocástico continuo, con convenciones de densidad explícitas. |
| III. Clases especiales | Modelos conocidos AR, MA y ARMA; realizaciones gaussianas estacionarias. Generación previa de ruido gaussiano, uniforme y Bernoulli. | Cadenas de Markov discretas/continuas, procesos de nacimiento/muerte y Poisson; modelos gaussianos multivariados y otras clases. |
| IV. Detección | Correlación como herramienta auxiliar. | Decisiones con hipótesis y umbrales, MAP/Bayes, Neyman–Pearson, curvas de error y detección con varias observaciones. No se presenta la correlación sola como un detector completo. |
| V. Estimación y filtrado | Ajuste AR por Yule–Walker y residuo de innovación estimado. | LMMSE general, innovaciones multivariadas, Wiener causal/no causal y Kalman. El residuo AR no equivale a un filtro de Kalman. |
| VI. Estadística | Media, varianza con N/N−1, RMS e histograma de registros. | Intervalos de confianza, pruebas de hipótesis y estimación por momentos/máxima verosimilitud con sus hipótesis. |
| VII. Estimación de procesos | Autocorrelación no paramétrica, periodograma/Welch existentes; estimación paramétrica AR por Yule–Walker y su PSD. | Ajuste MA/ARMA/ARIMA, comparación y selección automática de orden, diagnóstico residual y otros estimadores. |

## Modelos conocidos

La herramienta Modelos de procesos reúne dos operaciones: Modelo conocido y Estimar AR desde un registro. No crea un menú diferente para cada orden o familia. El modelo conocido permite AR (b=[1]), MA (a=[1]) o ARMA con b y a cargados por potencias de z⁻¹. Se normaliza a[0] igual que en el resto de la aplicación.

Convención: x[n] = −Σ a[k]x[n−k] + Σ b[k]e[n−k], con a[0]=1. Para e blanco de media μe y varianza σe²: μx=H(1)μe y Sc(ω)=σe²|H(exp(jω))|². Sc representa las fluctuaciones x−μx; Cx[k]=(1/2π)∫Sc(ω)exp(jωk)dω en −π…π. La autocorrelación suma μx². Una media no nula agrega una línea de peso 2πμx² en cero, que no se dibuja como una altura finita.

Se usa la realización directa II transpuesta para obtener A, B, C y D. La covarianza del estado resuelve P=A P Aᵀ+σe² B Bᵀ. Se comprueban estabilidad, finitud, semidefinición positiva y residuo de la ecuación. Las matrices internas no se duplican en el informe guardado. Para la simulación gaussiana, el estado inicial se obtiene de esa covarianza y es independiente de las innovaciones futuras: no se requiere un descarte arbitrario de muestras ni se confunde reposo con estado estacionario. Una realización finita no reproduce exactamente los momentos teóricos.

Los modelos complejos y no estacionarios no se incluyen en esta primera operación. Un polo en el círculo unidad, como en un paseo aleatorio, se informa como incompatible con este análisis estacionario; no se le asigna una varianza finita ficticia.

## Ajuste AR

Se centra un registro discreto real y se estima su autocovarianza con divisor N. Con orden p elegido por el usuario, se resuelve el sistema Toeplitz de Yule–Walker, se comprueba el residuo de la solución y se calcula la varianza de innovación. El resultado incluye H(z), estadísticas y espectro del modelo ajustado. El residuo válido empieza p muestras después del inicio observado y conserva el reloj disponible. La generación opcional produce una realización nueva del modelo, no una reconstrucción del registro.

El orden no se elige automáticamente. No se afirma blancura de los residuos, independencia ni que el proceso desconocido sea exactamente AR. Su promedio cuadrático sobre el tramo válido puede diferir de la varianza obtenida por Yule–Walker.

## Correlación auto/cruzada

La operación de correlación de registros conserva la autocorrelación y agrega una segunda entrada opcional. En cruzada se recortan ambos registros al intervalo de índices que realmente observaron en común; no se inventan datos para tramos desconocidos. Rxy[k]=Σ x[n+k]conj(y[n])/divisor. Las medias se estiman en ese intervalo. El divisor es N o N−|k|. La normalización usa √(Px Py), o el producto de desviaciones al centrar. Con divisor N−|k| puede superar uno en magnitud en retardos grandes. La salida puede ser compleja y no par; su valor en cero no es la potencia de una entrada.

## Evidencia y referencias

Comprobaciones dirigidas: momentos y covarianzas cerradas de AR(1), MA(1) y ARMA(1,1), integración del espectro AR(1), rechazo de raíz unitaria, semilla reproducible, ajuste AR y residuo sobre índices válidos, correlación cruzada compleja contra suma directa y alineación por origen. Paneles reales, ayudas ilustradas y reutilización de un sistema con reloj físico. No se ejecutó una batería general ni se certifica cobertura total del programa.

Referencias de implementación: [ecuación de filtrado de SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.lfilter.html), [ecuación de Lyapunov discreta](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_discrete_lyapunov.html), [resolución Toeplitz](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_toeplitz.html) y [convención de correlación](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.correlate.html). La documentación consultada puede corresponder a una versión distinta de las dependencias fijadas; se comprobaron las operaciones usadas en el entorno del portable.
