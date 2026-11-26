# Fase 03 · Digital Communications Lab

La fase autorizada integra una cadena de comunicaciones digitales con el Core, el escritorio, Python y CLI. El punto de arranque verifica la revisión final de 02C antes del desarrollo funcional. [Línea base](PHASE_03_BASELINE.md) · [Plan](PHASE_03_PLAN.md) · [Evidencia por plataforma](VALIDATION_MATRIX.md)

El diseño distingue la secuencia transmitida, el reloj de símbolos, las muestras I/Q, la referencia de recepción y el resultado medido. [Arquitectura](ARCHITECTURE.md) · [Contratos](SCIENTIFIC_CONTRACTS.md) · [Matemática](MATHEMATICAL_FOUNDATIONS.md) · [Auditoría independiente](MATHEMATICAL_AUDIT.md)

[Requisitos](PHASE_03_REQUIREMENTS.md) · [Trazabilidad](TRACEABILITY_MATRIX.md) · [Criterios de salida](QUALITY_GATE_CRITERIA.md) · [Referencias](INTEGRATION_CATALOG.md) · [Decisiones](DECISION_LOG.md) · [Registro de trabajo](IMPLEMENTATION_LOG.md)

## Enlace reproducible

Desde Workbench, abrí **Comunicaciones digitales → Enlace digital**. El perfil inicial usa QPSK Gray y filtros RRC. Después de calcular, el informe separa las tasas observadas de las referencias teóricas. **Abrir gráfico** permite elegir la constelación, el ojo, las señales I/Q, el espectro, la PSD o la respuesta del filtro.

El mismo cálculo está disponible desde un entorno Python con las [dependencias del proyecto](../../development/README.md). La orden de consola guarda un proyecto que podés abrir desde **Archivo → Sesiones**.

```sh
python -m signallab_pc communications link --bits 4096 --seed 2026 --eb-n0 6 --output enlace.slproj
```

```python
from signallab_pc.communications_experiment import ExperimentSpec, run_experiment
from signallab_pc.communications_storage import save_experiment

enlace = run_experiment(ExperimentSpec(bit_count=4096, seed=2026, eb_n0_db=6))
identificador = save_experiment("enlace-python.slproj", enlace)
print(enlace.report()["metrics"])
```

## Etapas y barridos desde la consola

Estos comandos permiten verificar por separado el mapeo QPSK, la constelación 16-QAM, un FIR RRC, la aplicación de AWGN y el cálculo Monte Carlo. La salida de `modulate` incluye `record`, el identificador de la señal compleja que se usa en `shape` y `awgn`.

```sh
python -m signallab_pc communications modulate --manual-bits "01 10 11 00" --output qpsk.slproj
python -m signallab_pc communications modulate --family qam --order 16 --bits 256 --seed 10 --output qam16.slproj
python -m signallab_pc communications pulse --pulse rrc --sps 8 --span 10 --rolloff 0.35 --output rrc.slproj
python -m signallab_pc communications shape --session qpsk.slproj --record ID_DE_QPSK --pulse rrc --sps 8 --interpolate --output tx.slproj
python -m signallab_pc communications awgn --session tx.slproj --record ID_DE_TX --reference snr --db 12 --seed 31 --output rx.slproj
python -m signallab_pc communications monte-carlo --symbols 90000 --eb-n0 5 --seed 80 --output monte-carlo.json
python -m signallab_pc communications sweep --bits 2048 --seed 42 --axis eb_n0_db=0,2,4,6 --output barrido --csv barrido.csv
python -m signallab_pc communications sweep --inspect --output barrido
```

Para recuperar un barrido interrumpido, repetí su comando original. Cada corrida verificada conserva configuración, semilla y resultados en un SLPROJ. Podés combinar varios parámetros con `--axis` repetido. El CSV resume las métricas y referencias para comparar desde otras herramientas. Las señales I/Q se pueden exportar como SLBIN con origen y reloj, o conservar junto al experimento en SLPROJ. JSON sigue disponible para proyectos pequeños y compatibles con el lector histórico.
