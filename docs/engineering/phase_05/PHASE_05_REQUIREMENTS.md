# Requisitos trazables de Fase 05

| ID | Requisito | Evidencia exigida |
| --- | --- | --- |
| ST-00 | Auditar código y estado de 2.2.1, conservar regresiones y adaptar Actions y el verificador a 2.3.x. | Mismo SHA y paquetes verificables. Verificador con casos de rechazo de familia, evidencia y recibos incompatibles. |
| ST-01 | Evaluación y generación discreta, continua, compleja y multivariada. Bernoulli, binomial, negativa, Poisson, geométrica, hipergeométrica, uniforme discreta, categórica, multinomial y familias continuas enumeradas en el roadmap. | PDF/PMF, CDF/supervivencia, cuantiles, intervalos, momentos, colas y soporte. Covarianza, pseudocovarianza, marginales, condicionales y transformaciones justificadas. |
| ST-02 | Estadística descriptiva real o por componente, covarianza compleja, histogramas, CDF y CCDF empíricas, Q–Q y boxplots. Ajuste por momentos y ML, intervalos y pruebas de hipótesis. | Parámetros, estimador, hipótesis, tamaño muestral, p-valor y limitaciones. Oráculos deterministas y campañas de sesgo, cobertura, error tipo I y potencia. |
| ST-03 | Ruido blanco, complejo, impulsivo, rosa, marrón, azul, violeta y con PSD dada. Wiener, caminata, Poisson, Markov, Ornstein–Uhlenbeck, gaussiano y telegráfico. Comparar conjunto y realización. | Distribuciones/transiciones, regularización, reloj, covarianza, incrementos y estacionariedad con condiciones. Correlación directa/FFT y simetría hermítica. |
| ST-04 | Ampliar análisis AR/MA/ARMA y evaluar ARIMA. Preservar Yule–Walker y OLS. Burg, máxima verosimilitud y ajuste MA/ARMA/ARIMA, orden, raíces, sensibilidad, residuos, ACF/PACF, periodos de calentamiento y pronóstico. | Pruebas de estabilidad/invertibilidad, recuperación paramétrica, error de pronóstico y comparación de estimadores. |
| ST-05 | Preservar periodograma, Welch y PSD AR. Añadir Bartlett, Blackman–Tukey, multitaper DPSS, análisis cruzado, coherencia y Lomb–Scargle. | Comparación de estimadores, potencia, escala y ventana. Intervalos con hipótesis y significado explícito de observación irregular. |
| ST-06 | ML/MAP/MMSE/LMMSE, Wiener FIR, Kalman lineal discreto y LMS/NLMS/RLS. | Comparación de señales y errores, trayectorias, Cramér–Rao cuando aplica, innovación, covarianza semidefinida, observaciones ausentes, convergencia. |
| ST-07 | Monte Carlo reproducible, réplicas, subflujos, barridos, números comunes con hipótesis, bootstrap e incertidumbre. | Probabilidades e intervalos, eventos raros, resumen incremental, cancelación, reanudación, sensibilidad y exportación. |
| ST-08 | Modernizar los paneles existentes con opciones progresivas. Integrar API, CLI y datos de otros laboratorios. | Paridad headless, apertura, cambios de método, figuras, ayuda, resultados, traspaso, cancelación y sesiones históricas. |
| ST-09 | Verificar almacenamiento, seguridad y recursos con políticas vigentes. | JSON finito, SLBIN/SLPROJ, huellas, recuperación, rechazo por presupuesto y rendimiento medido. |
| ST-10 | Aprobar el Quality Gate y publicar 2.3.x Preview. | Matriz Windows/Linux sobre un SHA limpio, portables e instaladores, fuentes, firma, hashes, inventario, Release e informe final. |

## Demostradores reproducibles

| Caso | Flujo con los servicios productivos |
| --- | --- |
| A | Distribución, tamaños muestrales y realizaciones → estadística, ajuste e intervalos → comparación poblacional y empírica. |
| B | Modelo AR/MA/ARMA conocido → realización, ACF/PACF y PSD → identificación, residuos, pronóstico y error frente al modelo. |
| C | Referencia más observación ruidosa → Wiener, Kalman y adaptación → error y convergencia. |
| D | Modelo, réplicas y barrido → probabilidad, incertidumbre y convergencia → guardar y reanudar. |
| E | Realización de fading o Clarke → distribución, correlación y PSD → propiedades teóricas y réplicas. |
