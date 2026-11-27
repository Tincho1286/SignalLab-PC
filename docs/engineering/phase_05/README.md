# Fase 05 · Probabilidad, estadística y procesos estocásticos

La fase está autorizada en `develop` y parte de la integración aprobada de 2.2.1 Preview. El objetivo es ampliar las herramientas de señales aleatorias y proporcionar los mismos cálculos científicos a Workbench, Python y CLI. El primer candidato público será de la familia 2.3.x, después de la calificación conjunta de Windows y Linux.

- [Línea base](PHASE_05_BASELINE.md) y [paquetes de trabajo](PHASE_05_PLAN.md)
- [Requisitos y demostradores](PHASE_05_REQUIREMENTS.md)
- [Contratos científicos](SCIENTIFIC_CONTRACTS.md)
- [Arquitectura](ARCHITECTURE.md) y [fundamentos de probabilidad](MATHEMATICAL_FOUNDATIONS.md)
- [Oráculos y protocolo estadístico](STATISTICAL_VALIDATION_PROTOCOL.md)
- [Criterios del Quality Gate](QUALITY_GATE_CRITERIA.md)
- [Trazabilidad](TRACEABILITY_MATRIX.md), [decisiones](DECISION_LOG.md) y [registro de implementación](IMPLEMENTATION_LOG.md)

La aceptación funcional de la Preview y la integración en `main` son decisiones distintas. [Política de entregas](../RELEASE_POLICY.md)

## Probar las distribuciones en el código de desarrollo

En **Señales aleatorias → Generar realización**, elegí **Poisson**, ingresá una media de recuentos de 2 y seleccioná **Probabilidad acumulada** en el punto 1. El cálculo devuelve $3e^{-2}$. Seleccioná **Generar realización** para producir un registro y desplegá las opciones avanzadas si querés dos réplicas independientes o un reloj físico.

```sh
python -m signallab_pc probability inspect --family poisson --parameters '{"rate":2}' --function cdf --argument 1
python -m signallab_pc probability generate --family poisson --parameters '{"rate":2}' --count 1024 --replicas 2 --seed 123 --output realizaciones.slproj
```

El archivo se abre en SignalLab y contiene el modelo y los dos registros con sus relaciones de procedencia. En Python se usan `Distribution`, `distribution_value` y `generate_realizations` de `signallab_pc.probability`. Los parámetros de la normal son media y desviación. Los de Rician son relación de amplitud fija a desviación y escala. Los intervalos de leyes enteras incluyen ambos extremos.

## Analizar una realización

En **Estadísticas e histograma**, cargá un registro y elegí su parte real, imaginaria, módulo o fase. El informe separa los valores del registro completo de los de la componente. Los diagnósticos agregan CDF, CCDF y caja. Con una normal de referencia agregan un gráfico Q–Q. La fase informa cuántos ceros quedaron excluidos.

```sh
python -m signallab_pc statistics describe --session realizaciones.slproj --record ID_REALIZACION --diagnostics --output analisis.slproj
```

Usá el identificador que devuelve el comando de generación. El análisis de Python utiliza `describe_record` de `signallab_pc.descriptive_statistics`. El informe conserva la huella de su entrada y los cuantiles almacenan la convención de interpolación.

### Ajuste e inferencia

En la misma herramienta elegí **Ajustar una distribución** para estimar sus parámetros a partir de las observaciones. Según la familia, podés seleccionar el estimador y pedir intervalos para los parámetros. Usá **Contrastar una hipótesis** para verificar, por ejemplo, una media con el método t o una proporción con la prueba binomial exacta. Si elegís Welch, F o Mann–Whitney, se habilita la segunda entrada. Confirmá que las muestras son independientes bajo el modelo del contraste. Las pruebas de media y varianza suponen normalidad y los intervalos informados son bilaterales.

```sh
python -m signallab_pc statistics fit --session realizaciones.slproj --record ID_REALIZACION --family poisson --iid --level 0.95 --output ajuste.slproj
python -m signallab_pc probability generate --family normal --parameters '{"mean":0,"std":1}' --count 64 --seed 321 --output normales.slproj
python -m signallab_pc statistics infer --session normales.slproj --record ID_NORMAL --iid --method ks --reference-family normal --reference-parameters '{"mean":0,"std":1}' --output contraste.slproj
```

El segundo ejemplo requiere un registro continuo sin empates que se quiera contrastar contra una normal estándar conocida. Si querés contrastar normalidad con media y desviación desconocidas, usá `--method shapiro` o `--method ad`. Las funciones equivalentes de Python son `fit_distribution` e `infer_record` en `signallab_pc.statistical_inference`. Los informes se publican en Resultados con sus entradas. [Supuestos y fórmulas](MATHEMATICAL_FOUNDATIONS.md#inferencia-y-ajuste)

### Generar y examinar procesos

En **Generar realización**, elegí un proceso en el mismo selector de distribuciones. Para una cadena de Markov, cada fila de la matriz indica las probabilidades de pasar del estado de esa fila a cada columna. Elegí un estado inicial desde 0, ingresá sus probabilidades iniciales o dejalo vacío para usar una distribución estacionaria única. En **Propiedades poblacionales** podés indicar dos posiciones desde el inicio para ver sus medias, varianzas y covarianza junto con la transición entre ellas.

```sh
python -m signallab_pc stochastic inspect --family ornstein_uhlenbeck --parameters '{"initial":0,"mean":2,"reversion":0.5,"std":1}' --rate 4 --first 4 --second 8
python -m signallab_pc stochastic generate --family markov --parameters '{"initial":0,"transition":[[0.75,0.25],[0.5,0.5]]}' --count 64 --seed 321 --replicas 2 --output trayectorias.slproj
```

La primera muestra contiene el estado inicial y, si se indicó un reloj, representa el tiempo cero. El generador conserva cada trayectoria como una señal reutilizable y referencia el modelo en el proyecto. Para usar los servicios directamente, importá `Process`, `generate_process`, `process_moments` y `process_transition` desde `signallab_pc.stochastic_processes`. [Transiciones y alcance](MATHEMATICAL_FOUNDATIONS.md#trayectorias-y-transiciones)

### Generar ruido y consultar su PSD

En **Generar realización**, seleccioná ruido blanco real o complejo, impulsivo, por color, por FIR o con PSD especificada. **Propiedades poblacionales** muestra la densidad bilateral en Hz y permite reutilizarla desde Resultados. Para una PSD real simétrica, escribí los pares de la mitad positiva como valores de la densidad bilateral. Para una salida compleja, podés cargar una PSD asimétrica con frecuencias positivas y negativas.

```sh
python -m signallab_pc stochastic inspect --family colored_noise --parameters '{"color":"pink","variance":1,"low_hz":8,"high_hz":120,"complex":false}' --rate 256 --bins 256
python -m signallab_pc stochastic generate --family colored_noise --parameters '{"color":"pink","variance":1,"low_hz":8,"high_hz":120,"complex":false}' --rate 256 --count 256 --seed 123 --output ruido.slproj
```

Con la misma frecuencia y cantidad de muestras o bins, la densidad de consulta coincide con la usada para sintetizar el ruido. En rosa y marrón, un corte inferior positivo regulariza la potencia próxima a DC. En Python podés usar `Noise`, `generate_noise` y `noise_spectrum` de `signallab_pc.stochastic_noise`. [Normalización y condiciones](MATHEMATICAL_FOUNDATIONS.md#modelos-de-ruido)

### Comparar canales y trayectorias

En **Correlación y covarianza**, elegí **Correlación cruzada** y cargá dos registros. El informe indica el intervalo común, el divisor y el método directo o FFT. **Matrices de covarianza y correlación** usa varios registros del proyecto como canales simultáneos. **Momentos de conjunto** usa esos registros como réplicas independientes y compara dos posiciones de cada trayectoria. Cuando comparten un modelo de proceso registrado, el informe agrega sus medias, varianzas y covarianza teóricas.

```sh
python -m signallab_pc stochastic correlate --session trayectorias.slproj --record ID_1 --center --method direct --output correlacion.slproj
python -m signallab_pc stochastic ensemble --session trayectorias.slproj --records ID_1 ID_2 --first 0 --second 4 --independent --output conjunto.slproj
```

Usá los identificadores que devuelve el generador. El motor sin Qt está en `signallab_pc.stochastic_covariance`, con `estimate_correlation`, `covariance_matrix` y `ensemble_moments`. [Convenciones](MATHEMATICAL_FOUNDATIONS.md#correlación-covarianza-y-conjunto)

### Estimar un modelo AR con Burg

En **Estimar modelo AR**, elegí **Un orden elegido** y seleccioná **Burg**. El informe distingue su varianza de innovación del error cuadrático de predicción a un paso. Si reservás las muestras finales, se usan para medir el error de validación. Los coeficientes permanecen fijados por el entrenamiento. En **Analizar modelo AR, MA o ARMA** podés solicitar la PACF teórica. El diagnóstico de ajuste incluye la PACF de los residuos de entrenamiento.

```python
from signallab_pc.ar_estimation import fit
from signallab_pc.model import Signal

record = Signal([-2, 0, 1, 5, -4])
print(fit(record, 2, method='burg')['a'])
```

La comparación automática de órdenes mantiene mínimos cuadrados sobre el mismo intervalo de observaciones para poder interpretar sus criterios. [Recursiones y alcance](MATHEMATICAL_FOUNDATIONS.md#identificación-autorregresiva)

### Ajustar MA, ARMA y ARIMA

El estimador temporal también ofrece las familias MA, ARMA y ARIMA. Elegí p para el orden autorregresivo, q para el de media móvil y d para las diferencias. Reservá el tramo final si querés medir el error fuera del entrenamiento. El informe identifica la inicialización de las innovaciones, la estabilidad del núcleo y la invertibilidad. Los pronósticos de un ARIMA vuelven a los niveles originales y sus límites corresponden a la incertidumbre de futuras innovaciones.

```sh
python -m signallab_pc stochastic generate --family wiener --parameters '{"initial":0,"drift":0.05,"std":1}' --rate 16 --count 256 --seed 321 --output camino.slproj
python -m signallab_pc stochastic identify --session camino.slproj --record ID_TRAYECTORIA --d 1 --reserve 16 --horizon 24 --lags 20 --output ajuste.slproj
```

El proyecto guarda el modelo, el diagnóstico y las curvas de pronóstico con la entrada original. Usá `fit_arma`, `compare_arma`, `arma_diagnostics` y `arma_forecast` de `signallab_pc.time_series_identification` para automatizar el cálculo. [Supuestos de ajuste y predicción](MATHEMATICAL_FOUNDATIONS.md#verosimilitud-condicional-y-arima)

### Estimar PSD con Bartlett

En **Densidad de potencia**, elegí **Bartlett · bloques disjuntos** e indicá cuántas muestras usar por segmento. El estimador promedia periodogramas rectangulares sin solape. El informe indica qué cola parcial quedó descartada. Si el modelo es ruido blanco gaussiano de media cero, seleccioná ruido real o complejo propio para obtener un intervalo marginal por bin.

```sh
python -m signallab_pc stochastic generate --family white_noise --parameters '{"variance":1,"complex":false}' --rate 256 --count 1024 --seed 123 --output ruido-blanco.slproj
python -m signallab_pc dsp psd --session ruido-blanco.slproj --record ID_REALIZACION --method bartlett --segment 64 --white-confidence real_gaussian_white --output densidad.slproj
```

El informe y su PSD quedan vinculados en Resultados. Para Python, usá `estimate_psd` de `signallab_pc.dsp_application` y `white_noise_confidence` de `signallab_pc.statistical_spectra`. [Normalización y cobertura](MATHEMATICAL_FOUNDATIONS.md#bartlett-y-cobertura-de-ruido-blanco)

### Comparar dos espectros

En **Densidad de potencia** elegí **Espectro cruzado y coherencia**. Cargá los registros x e y y elegí la longitud, el solape y la ventana. La aplicación toma el intervalo de índices observado en ambos. El gráfico comparte el eje de frecuencia para fase y coherencia. La biblioteca conserva la densidad cruzada, las dos densidades individuales disponibles y el informe de coherencia.

```sh
python -m signallab_pc stochastic spectral-cross --session par.slproj --record ID_X --second-record ID_Y --segment 64 --overlap 32 --output cruzada.slproj
```

Usá una sesión con dos registros discretos y reloj compatible. En Python podés usar `cross_spectra` de `signallab_pc.statistical_spectra`. [Convención y condiciones](MATHEMATICAL_FOUNDATIONS.md#espectro-cruzado-y-coherencia)

### Elegir un estimador espectral

En **Densidad de potencia**, Blackman–Tukey controla cuántos retardos de autocovarianza intervienen. Multitaper promedia espectros de ventanas DPSS ortogonales y registra su concentración. AR (Burg) estima un modelo autorregresivo de orden elegido y muestra la densidad de ese modelo. Podés superponer una referencia Welch en las mismas unidades y eje de frecuencia. Cada estimador conserva su propia separación de bins.

```sh
python -m signallab_pc dsp psd --session registros.slproj --record ID_REALIZACION --method multitaper --bandwidth 3 --tapers 5 --output multitaper.slproj
python -m signallab_pc stochastic lomb --session registros.slproj --record ID_REALIZACION --times-file instantes.json --low 0.5 --high 12 --points 256 --output irregular.slproj
```

Lomb–Scargle usa un tiempo en segundos por observación real, en orden estrictamente creciente. La salida normalizada mide la fracción de variación explicada por una sinusoide ajustada a cada frecuencia. Para Python, usá `estimate_psd` con `PSDRequest` y `lomb_periodogram` de `signallab_pc.statistical_spectra`. [Escalas y supuestos](MATHEMATICAL_FOUNDATIONS.md#estimación-espectral-avanzada)

### Estimar parámetros y filtrar ruido

En **Señales aleatorias › Estimación**, **ML, MAP y MMSE** trabaja con mediciones gaussianas reales. Ingresá el vector de observaciones, la matriz de diseño A y la covarianza R en sus pestañas. Si llenás los campos del modelo a priori, el informe agrega el posterior y su MSE. Desde Python, `linear_gaussian` de `signallab_pc.optimal_estimation` recibe estos mismos datos.

```python
from signallab_pc.optimal_estimation import linear_gaussian

fit = linear_gaussian([3, 1], [[1], [2]], [[2, 1], [1, 3]],
                      prior_mean=[2], prior_covariance=[[4]])
print(fit['ml']['estimate'], fit['posterior']['mmse'])
```

**Filtro de Wiener** puede entrenar un FIR con la entrada medida y la señal objetivo, o resolverlo desde correlaciones y potencia conocidas. En el ajuste desde registros, indicá una reserva final para medir el error con muestras fuera del entrenamiento. El informe, la transferencia y las secuencias resultantes quedan en el proyecto. La transferencia contiene la parte FIR y el informe conserva la constante opcional.

```sh
python -m signallab_pc stochastic estimate-gaussian --model gaussiano.json --output estimacion.slproj
python -m signallab_pc stochastic wiener --session par.slproj --record ID_OBSERVADA --second-record ID_DESEADA --length 8 --reserve 32 --output wiener.slproj
python -m signallab_pc stochastic wiener-model --model correlaciones.json --output diseno.slproj
```

El JSON del caso gaussiano usa los nombres del ejemplo Python. Para Wiener–Hopf, usá `autocorrelation`, `cross_correlation` y `target_power`. Una correlación compleja admite el objeto `{"real":[...],"imag":[...]}`. Las funciones `wiener_fir` y `wiener_hopf` están en `signallab_pc.wiener_filter`. [Modelo gaussiano](MATHEMATICAL_FOUNDATIONS.md#estimación-gaussiana-lineal) · [Wiener causal](MATHEMATICAL_FOUNDATIONS.md#wiener-fir-causal)

### Estimar estados con Kalman

Desde un modelo de estados discreto podés elegir **Usar modelo en… › Filtro de Kalman**. También podés cargar A, B, C y D en las tablas de la herramienta. La primera fila de las observaciones corresponde al primer índice y cada columna corresponde a un sensor. La máscara usa 0 para los datos ausentes y 1 para los disponibles. En **Trayectorias**, compará predicción y corrección o elegí la varianza posterior de cada estado. La biblioteca de resultados guarda, además, ganancias, innovaciones y matrices de covarianza por instante.

```sh
python -m signallab_pc stochastic kalman --model kalman.json --output estados.slproj
```

```json
{
  "state_model": {"A":[[1]], "B":[[0]], "C":[[1]], "D":[[0]], "dt":0.5},
  "observations": [[2], [0], [10]],
  "mask": [[true], [false], [true]],
  "process_covariance": [[0]], "measurement_covariance": [[1]],
  "initial_mean": [0], "initial_covariance": [[1]]
}
```

Con este ejemplo, la estimación corregida es 1, 1, 4. En el segundo instante solo se predice. El API usa `kalman_filter` de `signallab_pc.kalman_filter` con un `StateModel` discreto. [Modelo y estabilidad numérica](MATHEMATICAL_FOUNDATIONS.md#kalman-lineal-discreto)

### Adaptar un filtro y comparar métodos

En **Filtrado adaptativo**, elegí identificar un sistema, predecir o cancelar ruido. Indica la longitud del FIR y, si corresponde, el retardo de predicción. Para medir generalización, reservá un tramo final en el que los coeficientes se mantengan fijos. La vista **Señales** muestra cómo cambia el error durante el ajuste. El informe compara MSE entre algoritmos y entre valores del parámetro elegido. Podés elegir una configuración de la lista y reutilizar sus coeficientes finales.

```sh
python -m signallab_pc stochastic adaptive --session par.slproj --record ID_ENTRADA --second-record ID_SALIDA --length 8 --reserve 64 --method nlms --step 0.5 --output adaptacion.slproj
python -m signallab_pc stochastic adaptive --session par.slproj --record ID_ENTRADA --second-record ID_SALIDA --length 8 --configurations comparacion.json --output comparacion.slproj
```

El archivo de comparación es una lista de objetos, por ejemplo `[{"method":"lms","step":0.01},{"method":"rls","forgetting":0.99}]`. Usá `adaptive_fir` y `compare_adaptive` para aplicar los mismos métodos desde Python. [Recursiones y condiciones](MATHEMATICAL_FOUNDATIONS.md#filtrado-adaptativo-fir)

### Ejecutar una campaña y medir incertidumbre

En **Señales aleatorias › Experimentos**, **Monte Carlo** estima media, varianza o probabilidad repitiendo registros simulados. La carpeta guarda la definición y los resultados resumidos de cada bloque. Después de interrumpir una campaña podés reabrirla y continuar desde el último bloque verificado. El gráfico muestra la evolución de la estimación con la cantidad de réplicas.

En **Barrido y opciones de ejecución**, elegí un parámetro y sus valores para comparar escenarios. También podés cargar una definición JSON que combine familias. Para eventos raros, el informe conserva la cantidad observada, el total de observaciones y una cota superior aun cuando el recuento observado sea cero.

```json
{
  "metric": "probability", "seed": 2026, "samples": 256, "replicas": 64,
  "low": 1, "high": 1, "batch": 8, "common_random_numbers": true,
  "scenarios": [
    {"name":"Escenario A", "family":"bernoulli", "parameters":{"p":0.05}},
    {"name":"Escenario B", "family":"bernoulli", "parameters":{"p":0.1}}
  ]
}
```

```sh
python -m signallab_pc stochastic monte-carlo --model diseno.json --directory observaciones-mc --csv replicas.csv --output estudio.slproj
python -m signallab_pc stochastic bootstrap --session registros.slproj --record ID_DATOS --metric mean --seed 2026 --block-length 8 --replicas 512 --output incertidumbre.slproj
```

**Incertidumbre por bootstrap** parte de un registro real. Con longitud de bloque uno remuestrea observaciones individuales. Con una longitud mayor conserva tramos contiguos para estudiar series dependientes. El informe indica los supuestos, el error estándar y los límites percentiles. En Python, los mismos servicios son `run_campaign` y `load_campaign` de `signallab_pc.monte_carlo` y `bootstrap_record` de `signallab_pc.monte_carlo_bootstrap`. [Métodos e interpretación](MATHEMATICAL_FOUNDATIONS.md#simulación-incertidumbre-y-remuestreo)
