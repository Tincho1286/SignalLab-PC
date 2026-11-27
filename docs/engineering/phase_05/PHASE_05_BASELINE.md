# Línea base de Fase 05

Al iniciar, GitHub tenía `main` en `0c9e3bcdafd89dfd4437b28a93f0606fa5116542` y `develop` en `d545ffa358725b3fa2f04542ac44463618307bef`. La Fase 04 está cerrada e integrada. La actualización posterior fue documental. `git diff --exit-code 08cd1bc d545ffa -- . ':(exclude)docs' ':(exclude)README.md' ':(exclude)CHANGELOG.md' ':(exclude)CONTRIBUTING.md'` confirmó la identidad del código y la infraestructura con 2.2.1 Preview. GitHub sigue sirviendo 2.0.0 como última estable. [Cierre de Fase 04](../phase_04/PHASE_04_CLOSEOUT.md) · [Actualización estratégica](../STRATEGIC_UPDATE_REPORT.md)

## Medición comparable

Se descargaron los informes de línea base y distribución de la ejecución 45923696053. Se cotejaron los cuatro ZIP por tamaño y SHA-256 contra el recibo antes de leer el JSON. El candidato común es `08cd1bc28189ef0c1cd6c5a36f2d9bd32f6f1a48`. Los dos informes integrales aprobaron. El cliente de cada instalador preservó la sesión al actualizar desde 2.0.0 mediante un canal de ensayo y rechazó la descarga alterada. [Ejecución aprobada](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45923696053/attempts/2) · [Recibo con huellas](../phase_04/evidence/candidate-08cd1bc/matrix-receipt.json)

| Plataforma | Pruebas integrales | Líneas | Ramas | Pico RSS en enlace de 65 536 símbolos | Cancelación de Clarke / archivo |
| --- | ---: | ---: | ---: | ---: | --- |
| Windows Server 2022 | 1 257 | 43 264 / 48 503 (89,20 %) | 13 764 / 18 044 (76,28 %) | 466 751 488 bytes | 0,04755 s / 0,01265 s |
| Ubuntu 22.04 | 1 257 | 43 235 / 48 503 (89,14 %) | 13 758 / 18 044 (76,25 %) | 475 881 472 bytes | 0,02364 s / 0,01711 s |

Para repetir la medida, usar el SHA indicado, CPython 3.14.10 y el entorno fijado. `python -B -X utf8 tools/check_engineering_baseline.py --output work/engineering-baseline` genera pruebas integrales y cobertura. `python -B -X utf8 tools/measure_channel_modeling.py --output work/channel-modeling-performance.json` repite perfiles de recursos. Los números de la tabla corresponden al enlace de Fase 04. Los perfiles de Fase 05 se medirán por separado.

En Windows, con CPython 3.14.10, NumPy 2.5.5 y SciPy 1.18.1, se ejecutaron 55 regresiones focalizadas de AR, espectros, Workbench, fading, Doppler y campañas en 13,40 s con Qt offscreen y un hilo BLAS/OMP. Pasaron sobre `d545ffa`.

## Inspección de las herramientas de partida

| Activo | Capacidad observada | Límite que guía el diseño |
| --- | --- | --- |
| `random_signals` y `RandomPanel` | PCG64 con normal, uniforme y Bernoulli. Media compleja, dos divisores de varianza, RMS e histograma. | Se preservarán el orden de las variantes y sus campos históricos. Las evaluaciones poblacionales y multivariadas requieren contratos adicionales. |
| Correlación propia y cruzada | FFT, conjugación y retardos documentados, denominadores N y N−\|k\|. La cruzada alinea registros observados. | La corrección por número de pares no garantiza insesgamiento al estimar medias. Se necesitan contraste directo y matrices. |
| `random_models`, `ar_estimation` | AR/MA/ARMA estables, simulación estacionaria, PSD teórica, Yule–Walker y OLS, AIC/AICc/BIC y pronóstico. | Separar simulación y parámetros teóricos de estimación y modelos integrados. Ampliar el comparador, la PACF y los diagnósticos. |
| `fourier.spectral_density`, `dsp_application.estimate_psd` | Periodograma, Welch y una convención heredada con metadatos de escala, ventana y reloj. PSD de AR desde el analizador de modelos. | Bartlett, Blackman–Tukey, DPSS, Lomb–Scargle, espectros cruzados y coherencia requieren supuestos y normalizaciones explícitos. |
| Comunicaciones y canales | I/Q, gaussianas, fading Rayleigh/Rician, Clarke, fase Wiener, ruido de banda, subflujos y campañas verificables. | Reutilizar las primitivas equivalentes sin cambiar realizaciones históricas. La fase Wiener del canal tiene su escala física propia. |
| Core y almacenamiento | `Signal`, `Transfer`, `StateModel`, `ExecutionContext`, procedencia, JSON, SLBIN, SLPROJ y publicación transaccional. | Mantener esquemas históricos. Representar resultados científicos finitos o con estados explícitos y realizar entregas atómicas. |

[Plan estratégico de modernización](../TOOL_MODERNIZATION_PLAN.md#fase-05--probabilidad-y-estadística) · [API de Engineering Core](../phase_02b/ENGINEERING_CORE_API.md) · [Auditoría de canales](../phase_04/MATHEMATICAL_AUDIT.md)
