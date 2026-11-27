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
