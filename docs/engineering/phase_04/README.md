# Fase 04 · Canales

La fase parte de `a94cd37`, la integración aprobada tras validar la 2.1.1 Preview. Amplía el canal AWGN de Fase 03 con modelos de propagación e imperfecciones del enlace. [Roadmap](../ROADMAP.md)

[Línea base](PHASE_04_BASELINE.md) · [Plan](PHASE_04_PLAN.md) · [Arquitectura](ARCHITECTURE.md) · [Requisitos](PHASE_04_REQUIREMENTS.md) · [Contratos científicos](SCIENTIFIC_CONTRACTS.md) · [Auditoría matemática](MATHEMATICAL_AUDIT.md) · [Trazabilidad](TRACEABILITY_MATRIX.md) · [Quality Gate](QUALITY_GATE_CRITERIA.md)

## Preparar las señales de ejemplo

Ejecutá este código con el entorno Python de SignalLab en una carpeta de trabajo vacía. Genera dos tonos I/Q de 16 384 muestras con el mismo reloj de 96 kHz. `entrada.slbin` es el tono de 1,5 kHz y `externa.slbin` es un interferente de 4 kHz con amplitud 0,15. Los comandos de consola de esta página usan esos archivos.

```python
import numpy as np

from signallab_pc.communications_data import SymbolClock, iq_signal
from signallab_pc.scientific_storage import save_binary_signal

clock = SymbolClock(12_000, 8)
n = np.arange(16_384)
save_binary_signal(iq_signal(np.exp(2j * np.pi * n / 64), clock), 'entrada.slbin')
save_binary_signal(iq_signal(0.15 * np.exp(2j * np.pi * n / 24), clock), 'externa.slbin')
```

## Multitrayecto con retardos enteros

Para una señal discreta finita, cada trayectoria desplaza la entrada $d_k$ muestras y la multiplica por una ganancia compleja $a_k$. El canal calcula $y[n] = \sum_k a_k x[n - d_k]$. Los retardos son enteros no negativos. Las trayectorias con igual retardo se superponen con su fase. La entrada vale cero fuera del registro y la salida conserva las colas de todos los caminos. [Modelo de banda base, Tse y Viswanath, §2.2](https://web.stanford.edu/~dntse/papers/ch1%2B2.pdf)

El primer índice y el reloj de la salida coinciden con los de la entrada. Para $N$ muestras se devuelven $N + \max(d_k)$, incluso si una ganancia se declara igual a cero. Si se conoce $F_s$, cada retardo equivale a $d_k/F_s$ segundos. Las ganancias controlan la amplitud y fase sin normalización automática.

El análisis entrega el impulso coherente, el perfil de potencia, el retardo medio y la dispersión RMS. Con muestras por símbolo conocidas, cuantifica la interferencia sobre la fase del tap de mayor potencia. Se puede elegir normalizar a energía unitaria y abrir la respuesta frecuencial, el impulso y el perfil de potencia desde el resultado del escritorio.

### Reproducir el cálculo

En el escritorio, abrí **Comunicaciones → Canal multitrayecto**. Cargá la entrada y escribí una trayectoria por línea. Los gráficos y el informe aparecen junto al resultado reutilizable. La vista I/Q muestra las primeras 512 muestras, como en las demás herramientas de comunicaciones. El registro guardado conserva toda la salida.

```text
0 = 1
2 = -i/2
```

Con una entrada que contiene $1+2i$ y $3-i$, la salida esperada es $1+2i,\ 3-i,\ 1-i/2,\ -1/2-3i/2$.

```python
from signallab_pc.communications_channel import ChannelPath, apply_multipath
from signallab_pc.model import Signal

x = Signal([1 + 2j, 3 - 1j], origin=-1)
y = apply_multipath(x, (ChannelPath(0), ChannelPath(2, 0, -0.5)))
print(y.axis, y.values)
```

```sh
python -m signallab_pc communications multipath --signal entrada.slbin --path=0=1 "--path=2=-i/2" --frequency-points 2048 --output canal.slproj
```

### Ejecución y validación

El cálculo suma copias por bloques y evita construir un FIR denso entre ecos. El trabajo crece con el producto de las muestras por las trayectorias activas. La reserva se estima con el tamaño de salida, la cantidad de trayectorias y un bloque temporal. El contexto de ejecución admite cancelación entre bloques, presupuesto de trabajo y plazo cooperativo. El proyecto conserva los parámetros, la huella de la entrada y el vínculo al registro de origen.

Las pruebas comparan contra una convolución calculada de forma independiente, verifican identidad, cancelación, reloj, fase, superposición y persistencia. La misma operación se ejecuta desde Python, CLI y escritorio.

## Fading Rayleigh y Rician

En **Comunicaciones → Fading Rayleigh y Rician**, configurá una trayectoria por línea con retardo y potencia media. Para Rician agregá factor K y fase LOS en radianes. El selector del resultado alterna entre la salida y las realizaciones de cada trayectoria. El gráfico de evolución muestra la magnitud de los coeficientes.

```sh
python -m signallab_pc communications fading --signal entrada.slbin --path=0=1 "--path=4=0.25,10,pi/2" --k-scale db --seed 2026 --output fading.slproj
```

El mismo ejemplo en Python usa `apply_fading(x, FadingSpec((FadingPath(), FadingPath.from_k_db(10, delay_samples=4, average_power=0.25, los_phase_rad=math.pi/2)), 2026))` desde `signallab_pc.communications_fading`. Este comando genera coeficientes independientes por muestra. [Potencia, fase y semillas](SCIENTIFIC_CONTRACTS.md#fading-rayleighrician)

### Doppler

Para correlacionar el fading, elegí **Clarke** y un Doppler máximo en Hz. El gráfico de autocorrelación y PSD usa la trayectoria elegida o la primera con potencia. En la CLI, `--diagnostics` guarda los diagnósticos Doppler por trayectoria activa.

```sh
python -m signallab_pc communications fading --signal entrada.slbin --path=0=1 --doppler-max-hz 64 --diagnostics --output clarke.slproj
python -m signallab_pc communications shift-carrier --signal entrada.slbin --frequency-hz -128 --phase-rad 0.25 --output desplazamiento.slproj
```

La entrada debe tener Fs registrada. En Workbench, **Doppler y fase** aplica el desplazamiento constante y la fase inicial de la segunda orden. [Modelo y condiciones](SCIENTIFIC_CONTRACTS.md#dispersión-doppler-de-clarke)

### Distribuciones de fading

Abrí **Distribuciones de envolvente y fase** en los resultados de **Fading Rayleigh y Rician**. El histograma usa la envolvente normalizada por la potencia de la trayectoria y el ángulo relativo a LOS para Rician. Si dejás vacío el número de trayectoria, se muestra la primera con potencia. En Python, usá `resultado.realizations[0].distributions()`. En la CLI, `--distributions` guarda las densidades y enlaza cada cálculo con la realización que lo originó. [Unidades, fórmulas y alcance](SCIENTIFIC_CONTRACTS.md#distribuciones-de-envolvente-y-fase)

```sh
python -m signallab_pc communications fading --signal entrada.slbin '--path=0=1,4,pi/2' --seed 2026 --distributions --output distribuciones.slproj
```

## Imperfecciones de reloj, fase e I/Q

En **Comunicaciones → Reloj, fase e I/Q**, elegí retardo y SFO, fase Wiener o desequilibrio I/Q. Cada modelo trabaja sobre la señal cargada. El informe registra el reloj resultante, la varianza del incremento de fase o el rechazo de imagen, según el cálculo. La trayectoria de fase queda disponible como una señal en radianes.

```sh
python -m signallab_pc communications timing-offset --signal entrada.slbin --delay-samples 0.375 --sfo-ppm 250 --output reloj.slproj
python -m signallab_pc communications phase-noise --signal entrada.slbin --linewidth-hz 16 --seed 673 --output fase.slproj
python -m signallab_pc communications iq-imbalance --signal entrada.slbin --gain-db 1.94 --phase-rad 0.23 --dc-i 0.025 --dc-q -0.07 --output iq.slproj
```

Python expone las mismas operaciones en `signallab_pc.communications_impairments`. Los retardos fraccionarios y SFO usan interpolación aproximada. [Convenciones y alcance](SCIENTIFIC_CONTRACTS.md#retardo-y-desajuste-del-reloj)

## Interferencia

En **Comunicaciones → Interferencia**, elegí tonos, banda limitada o una señal externa. Podés declarar la potencia interferente o el objetivo SIR. El informe mide cada potencia sobre el registro deseado y compara SIR, SNR y SINR. La salida, el interferente y el ruido opcional quedan disponibles en el proyecto.

```sh
python -m signallab_pc communications interference --signal entrada.slbin --tone "100,0.5" --tone "200,0.2,1.57" --sir-db 6 --output tonos.slproj
python -m signallab_pc communications interference --signal entrada.slbin --bandwidth-hz 512 --center-hz 1000 --sir-db 8 --noise-snr-db 10 --output adyacente.slproj
python -m signallab_pc communications interference --signal entrada.slbin --interferer externa.slbin --output mezcla.slproj
```

Python usa `InterferenceSpec` y `apply_interference` en `signallab_pc.communications_interference`. Las fuentes con frecuencias en Hz requieren Fs. [Convenciones, calibración y potencia](SCIENTIFIC_CONTRACTS.md#interferencia)

## Pérdidas de propagación

En **Comunicaciones → Pérdidas de propagación**, elegí ganancia fija, espacio libre o log-distancia. La sombra es opcional y se mantiene constante durante una corrida. El informe desglosa pérdida por distancia, sombra y ganancia resultante. El módulo Python `signallab_pc.communications_propagation` permite evaluar la pérdida sin una señal mediante `evaluate_propagation` y aplicar la misma configuración con `apply_propagation`. [Modelo y condiciones](SCIENTIFIC_CONTRACTS.md#propagación-a-gran-escala)

```sh
python -m signallab_pc communications propagation --signal entrada.slbin --model free-space --distance-m 1000 --carrier-hz 1e9 --output espacio-libre.slproj
python -m signallab_pc communications propagation --signal entrada.slbin --model log-distance --distance-m 100 --reference-distance-m 10 --reference-loss-db 42 --exponent 3 --shadow-std-db 4 --seed 70 --output sombra.slproj
```

## Cadena de canal

En **Comunicaciones → Cadena de canal**, elegí modelos, ordenalos y vinculá los interferentes externos a señales del proyecto. Podés guardar la configuración, modificar sus parámetros en JSON y abrirla desde el escritorio o la CLI. El selector de resultados muestra la salida final, las etapas y sus componentes. Para reproducir los ejemplos de cadena, enlace y barrido, guardá este bloque como `canal.json` junto a las señales de ejemplo.

```json
{
  "schema": 1,
  "seed": 2026,
  "stages": [
    {"kind": "multipath", "parameters": {"paths": [{"delay_samples": 0}, {"delay_samples": 4, "gain_real": 0.3}]}},
    {"kind": "carrier", "parameters": {"frequency_hz": 45}},
    {"kind": "awgn", "parameters": {"reference": "snr", "level_db": 15, "seed": 30}}
  ]
}
```

```sh
python -m signallab_pc communications channel-pipeline --signal entrada.slbin --config canal.json --output etapa.slproj
```

Python usa `ChannelStage`, `ChannelPipelineSpec` y `run_channel_pipeline` en `signallab_pc.communications_pipeline`. Cada vínculo externo agrega `external_input` a la etapa y usa `--external-file nombre=archivo.slbin` o `--external-record nombre=id` en la CLI. [Contratos y semillas](SCIENTIFIC_CONTRACTS.md#composición-ordenada)

### Ejecutar el enlace

En **Enlace digital**, activá **Incluir cadena de canal** para aplicarla entre los pulsos TX y RX. Podés usar la misma configuración que guardaste desde **Cadena de canal**. El selector lista la señal recibida y los resultados intermedios. Con **Agregar AWGN al final del canal**, el ruido conserva la referencia de energía transmitida del control histórico.

```sh
python -m signallab_pc communications link --bits 1024 --channel-config canal.json --no-noise --output enlace.slproj
```

Si la configuración requiere interferentes, agregá `--external-file nombre=archivo.slbin`, o `--external-session proyecto.slproj --external-record nombre=id`. El archivo del enlace incluye la cadena verificable. En Python, se configura con `ExperimentSpec(channel_pipeline=...)` y `run_experiment(spec, external=...)`. [Recepción y condiciones de validez](SCIENTIFIC_CONTRACTS.md#acoplamiento-al-enlace-digital)

### Barridos de canal

En **Barrido**, activá la cadena para habilitar sus parámetros en el selector de ejes. Podés elegir réplicas por punto, agregar ejes y usar semillas comunes o independientes. En la CLI se repite `--axis` para formar una combinación de parámetros.

```sh
python -m signallab_pc communications sweep --bits 2048 --channel-config canal.json --axis channel.2.frequency_hz=0,30,60 --axis eb_n0_db=4,8 --repetitions 3 --output campaña
python -m signallab_pc communications sweep --resume --output campaña --csv corridas.csv
```

Los informes indican cuántas réplicas dieron mediciones válidas. El catálogo permite incorporar una corrida con sus señales y configuración, o retomar las corridas faltantes. [Semillas, intervalos y recuperación](SCIENTIFIC_CONTRACTS.md#campañas-y-calibración-por-sinr)

## Calificación de 2.2.0 Preview

La 2.2.0 Preview se publicó sobre `a3026d2`, que pasó la matriz integral de Windows y Linux con portables, instaladores y fuentes verificados. El expediente registra la confirmación de Linux y el recorte al 200 % que queda pendiente en Windows. [Descargas](../../releases/v2.2.0.md) · [Quality Gate](QUALITY_GATE_REPORT.md) · [Expediente de cierre](PHASE_04_CLOSEOUT.md) · [Servicios](INTEGRATION_CATALOG.md) · [Validación](VALIDATION_MATRIX.md) · [Riesgos residuales](RESIDUAL_RISK_REGISTER.md) · [Límites técnicos](TECHNICAL_DEBT_REGISTER.md).
