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
