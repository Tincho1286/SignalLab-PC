# Implementación de Fase 04

## Línea base y consolidación del multitrayecto

La base comprobada es `5a0bff926155f560fd6b071a010f422e587c8484`. El motor agrupaba tácitamente copias en la salida, sin una representación coherente que sirviera para calcular diagnósticos. Los taps del nuevo contrato son comunes al motor, el PDP, la normalización y la respuesta frecuencial. Los momentos usan retardos relativos para preservar la resolución con retardos compartidos grandes.

Validaciones en Windows con Python 3.14.10.

| Comando | Evidencia |
| --- | --- |
| `python -B -X utf8 -m unittest discover -s tests -p "test_communications_*.py"` | 75 pruebas aprobadas. Incluye `numpy.convolve`, `scipy.signal.freqz`, momentos exactos, normalización extrema, informe, reutilización y apertura de figuras. |
| `python -B -X utf8 tools/check_static.py` | Aprobado para 403 archivos Python. |
| `git diff --check` | Aprobado. |

La Fase 04 requiere repetir la calificación sobre el candidato definitivo Windows/Linux, junto con el alcance pendiente de la [matriz](TRACEABILITY_MATRIX.md).

El commit `56c69f1` aprobó los controles matemáticos de Windows y Ubuntu en la primera ejecución posterior al envío a `develop`. [Resultados](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45881734112).

## Rayleigh y Rician independientes

Se añadieron caminos con potencia media especificada, K lineal o en dB, fase LOS y flujos PCG64 por camino. El reloj de cada realización se desplaza al índice de llegada. Las herramientas archivan la salida y los coeficientes emparejados con su estadística. Se conservó el cálculo AWGN de control.

| Comando | Evidencia |
| --- | --- |
| `python -B -X utf8 -m unittest discover -s tests -p "test_communications_*.py"` | 81 pruebas aprobadas en Windows. Incluye reconstrucción con varios caminos, equivalencia Workbench/Python, sesión de CLI, cancelación y referencias estadísticas. |
| `python -B -X utf8 tools/check_static.py` | Aprobado para 404 archivos Python. |
| Contraste de CDF con el motor sin Qt | Ambas envolventes cumplen el umbral de 0,015. La fase Rayleigh también lo cumple. [Mediciones](MATHEMATICAL_AUDIT.md#mediciones-en-windows). |

El commit `dad7625` aprobó los controles matemáticos de Windows y Ubuntu. [Resultados](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45882601534).

## Doppler determinista y fading correlacionado

`CarrierShift` separa el giro coherente de frecuencia y fase de la dispersión de Clarke. El motor Clarke integra la masa de cada banda de cuadratura y registra la grilla, la semilla, la huella de origen y las versiones numéricas. Workbench abre la autocorrelación y la PSD de la primera trayectoria activa. CLI exporta los diagnósticos por camino. Se midieron autocorrelación, fracción de potencia y coherencia sin cargar Qt. [Oráculos y resultados](MATHEMATICAL_AUDIT.md#mediciones-de-doppler-en-windows).

La suite de comunicaciones aprobó 87 pruebas en Windows con `python -B -X utf8 -m unittest discover -s tests -p "test_communications_*.py"`. Incluye los contrastes de Clarke, el caso límite de Doppler cero, presupuesto y cancelación, salidas de CLI archivadas y apertura de las nuevas figuras. `python -B -X utf8 tools/check_static.py` aprobó 405 archivos Python.

El commit `e6c2e62` aprobó los controles matemáticos de Windows y Ubuntu. [Resultados](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45883992749).

## Retardo, SFO, ruido de fase e I/Q

Los modelos de reloj, fase e I/Q ejecutan desde Python, Workbench y los comandos `timing-offset`, `phase-noise` e `iq-imbalance`. El resultado conserva la procedencia y la fase Wiener se archiva como señal auxiliar. El reloj de salida distingue muestras fraccionarias por símbolo de los intervalos enteros del receptor actual.

`python -B -X utf8 -m unittest discover -s tests -p "test_communications_*.py"` aprobó 94 pruebas en Windows. `python -B -X utf8 tools/check_static.py` aprobó 406 archivos. El contraste directo con Qt bloqueado midió error de SFO, varianza Wiener e IRR, y delimitó el error de los perfiles ensayados. [Mediciones](MATHEMATICAL_AUDIT.md#mediciones-de-reloj-fase-e-iq-en-windows).

El commit `0cebf02` aprobó los controles matemáticos de Windows y Ubuntu. [Resultados](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45885148245).

## Interferencia tonal, en banda y externa

Workbench, Python y CLI comparten la síntesis, calibración y medición. Se verifica la alineación de la segunda señal y se registra el traslado de portadora. Se muestran por separado SINR por suma de potencias y potencia observada del disturbio. El guardado atómico verifica las huellas de las fuentes y componentes y rechaza cambios antes de publicar.

`python -B -X utf8 -m unittest discover -s tests -p "test_communications_*.py"` aprobó 101 pruebas en Windows. Las pruebas seleccionadas de CLI, escritorio, interferencia y DSP aprobaron 18 casos. La medición independiente de la banda adyacente y las relaciones de potencia se realizó con importaciones Qt bloqueadas. [Mediciones](MATHEMATICAL_AUDIT.md#mediciones-de-interferencia-en-windows).

Los controles matemáticos de `7262ba8` aprobaron Windows y Ubuntu. [Resultados](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45886585846).

## Pérdidas de propagación a gran escala

El nuevo motor aplica ganancia fija, espacio libre, log-distancia y sombra log-normal. Guarda pérdida de referencia, pérdida por distancia, realización de sombra y ganancia neta. La API permite evaluar la pérdida sin generar una señal. Workbench y CLI comparten el servicio para aplicar el modelo a una entrada.

La suite de comunicaciones aprobó 107 pruebas en Windows. El control estático aprobó 408 archivos Python. Se verificaron la referencia UIT-R, los incrementos por década, el reloj de salida, la persistencia por CLI, el flujo de escritorio y el modelo log-normal con Qt bloqueado. [Oráculos](MATHEMATICAL_AUDIT.md#mediciones-de-propagación-en-windows).

El commit `964f3f6` aprobó los controles matemáticos de Windows y Ubuntu. [Resultados](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45887301131).

La medición exploratoria del mismo bloque usó `tools/engineering.coveragerc` sobre la suite de comunicaciones. Se observaron brechas de ramas en CLI (76,8 %), fading (78,6 %), Doppler (80,0 %), imperfecciones (82,6 %) e interferencia (83,3 %). Se volverán a medir con la suite integral y el candidato final. Los denominadores de cobertura se conservan.

## Cadena ordenada de modelos de canal

El contrato de cadena reutiliza las operaciones individuales. Registra el orden, las semillas efectivas, la potencia, el reloj y las realizaciones de cada etapa. Los artefactos se guardan juntos. La prueba de importación conserva los vínculos y huellas después de cambiar los identificadores de proyecto. Las señales intermedias cuentan contra la reserva disponible durante la ejecución.

El editor de Workbench permite agregar y reordenar modelos preconfigurados, vincular entradas externas y abrir o guardar su configuración común con CLI y Python. La edición detallada de parámetros se realiza en el JSON opcional del editor. [Uso](README.md#cadena-de-canal) · [Contratos](SCIENTIFIC_CONTRACTS.md#composición-ordenada).

En Windows, la suite de comunicaciones aprobó 114 pruebas. El control estático aprobó 410 archivos Python. La CLI también ejecutó y archivó una cadena completa con importaciones de Qt bloqueadas. Se verificaron cancelación, límite de memoria de la cadena, etapas alteradas, reasignación de identificadores, vínculo a una señal externa y equivalencia de orden en Workbench.

El commit `6e9702c` aprobó los controles matemáticos de Windows y Ubuntu. [Resultados](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45890224295).

## Cadena de canal en el enlace

El enlace ejecuta la cadena entre TX y RX, guarda sus realizaciones e identifica la sincronización aplicada. El control sin cadena conserva las muestras y el formato históricos. Los casos con SFO incompatible o retardo fraccionario fuera de la referencia entera guardan las señales y el estado de indisponibilidad sin fabricar métricas. El modo piloto se comprobó con Rayleigh, Rician y desplazamiento Doppler. También se guardó un interferente externo dentro del enlace y se abrió el archivo recuperando sus vínculos.

La suite de comunicaciones aprobó 121 pruebas en Windows. `tools/check_static.py` aprobó 410 archivos y `git diff --check` terminó sin errores.

El commit `e60f820` aprobó los controles matemáticos de Windows y Ubuntu. [Resultados](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45891161240).

## Barridos de canal y réplicas

Los ejes numéricos de las etapas se combinan con los del enlace. Cada punto puede guardar réplicas y semillas comunes o independientes. La calibración SINR descuenta la potencia de ruido observada. El CSV incluye las relaciones medidas de interferencia. Los archivos externos del catálogo tienen huellas verificadas y se conservan para continuar una campaña sin volver a suministrar las entradas.

El experimento de regresión combinó dos niveles de SINR, dos ganancias y tres réplicas por punto. Se verificaron las 12 corridas reabiertas, el resultado observado de calibración, la exportación, los intervalos sobre EVM y el emparejamiento de semillas. Una segunda campaña se canceló después de registrar la primera corrida y retomó los datos externos archivados. La suite de comunicaciones aprobó 128 pruebas en Windows.
