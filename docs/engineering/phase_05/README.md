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
