# Fase 04 · Canales

La fase parte de `a94cd37`, la integración aprobada tras validar la 2.1.1 Preview. Amplía el canal AWGN de Fase 03 con modelos de propagación e imperfecciones del enlace. [Roadmap](../ROADMAP.md)

[Línea base](PHASE_04_BASELINE.md) · [Plan](PHASE_04_PLAN.md) · [Arquitectura](ARCHITECTURE.md) · [Requisitos](PHASE_04_REQUIREMENTS.md) · [Contratos científicos](SCIENTIFIC_CONTRACTS.md) · [Auditoría matemática](MATHEMATICAL_AUDIT.md) · [Trazabilidad](TRACEABILITY_MATRIX.md) · [Quality Gate](QUALITY_GATE_CRITERIA.md)

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

Para correlacionar el fading, elegí **Clarke** y un Doppler máximo en Hz. Podés abrir el diagnóstico de autocorrelación y PSD de la primera trayectoria activa. En la CLI, `--diagnostics` guarda los diagnósticos por trayectoria con potencia.

```sh
python -m signallab_pc communications fading --signal entrada.slbin --path=0=1 --doppler-max-hz 64 --diagnostics --output clarke.slproj
python -m signallab_pc communications shift-carrier --signal entrada.slbin --frequency-hz -128 --phase-rad 0.25 --output desplazamiento.slproj
```

La entrada debe tener Fs registrada. En Workbench, **Doppler y fase** aplica el desplazamiento constante y la fase inicial de la segunda orden. [Modelo y condiciones](SCIENTIFIC_CONTRACTS.md#dispersión-doppler-de-clarke)

## Imperfecciones de reloj, fase e I/Q

En **Comunicaciones → Reloj, fase e I/Q**, elegí retardo y SFO, fase Wiener o desequilibrio I/Q. Cada modelo trabaja sobre la señal cargada. El informe registra el reloj resultante, la varianza del incremento de fase o el rechazo de imagen, según el cálculo. La trayectoria de fase queda disponible como una señal en radianes.

```sh
python -m signallab_pc communications timing-offset --signal entrada.slbin --delay-samples 0.375 --sfo-ppm 250 --output reloj.slproj
python -m signallab_pc communications phase-noise --signal entrada.slbin --linewidth-hz 16 --seed 673 --output fase.slproj
python -m signallab_pc communications iq-imbalance --signal entrada.slbin --gain-db 1.94 --phase-rad 0.23 --dc-i 0.025 --dc-q -0.07 --output iq.slproj
```

Python expone las mismas operaciones en `signallab_pc.communications_impairments`. Los retardos fraccionarios y SFO usan interpolación aproximada. [Convenciones y alcance](SCIENTIFIC_CONTRACTS.md#retardo-y-desajuste-del-reloj)

## Alcance siguiente

Quedan los modelos de interferencia, las pérdidas de propagación y la integración de los modelos al enlace y a los barridos. La caracterización de rendimiento por perfil y la matriz del Quality Gate corresponden al candidato de cierre de la fase.
