# Registro de Fase 03

## 26 de noviembre de 2026 · WP-00

Se consolidó la documentación de 02C y se despachó la matriz única de Windows y Linux para `a5eafa9a1e98116e84b57d3bb0e8881ea02b2931`. El candidato incorpora el cierre de E-01, las aprobaciones E-02, E-03 y E-05, y E-04 en seguimiento. La auditoría de arquitectura identificó los servicios DSP, el contexto y pool de ejecución, los formatos y el patrón de campaña que se reutilizan. [Matriz](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45812233593) · [Arquitectura](ARCHITECTURE.md)

Se fijaron convenciones de rotación, energía, ruido, reloj y métricas. Se generaron vectores por cuadratura, reflexión binaria y suma directa y se contrastó su alcance con Komm 0.37.0. El empaquetado conserva el lock del Core durante la apertura de fase. [Auditoría matemática](MATHEMATICAL_AUDIT.md) · [Dependencias y referencias](INTEGRATION_CATALOG.md)

Se ejecutaron DFT, IDFT y FIR en CPython 3.14.10 con la importación de Qt bloqueada. El retorno DFT/IDFT conservó muestras, origen, reloj y unidades. El FIR de longitud completa conservó la cola y el reloj. Se ensayó SLPROJ con seis registros sintéticos del tamaño de una corrida de comunicaciones y se verificó la reapertura. `python -B -X utf8 tools/check_static.py` aprobó 390 archivos. [Perfiles y tamaños](PERFORMANCE_REPORT.md)

La corrida única de `a5eafa9` terminó con éxito en ambos sistemas. Se verificaron los digests de los cinco artefactos. El comando `python -B -X utf8 tools/check_quality_gate_02c.py --input work/phase03-baseline-a5eafa9 --output work/phase03-baseline-a5eafa9/verified --candidate a5eafa9a1e98116e84b57d3bb0e8881ea02b2931 --require-automated` reprodujo los 37 controles aprobados por plataforma. Los portables y los inventarios ratificaron E-01. [Línea base validada](PHASE_03_BASELINE.md) · [Recibos de CI](evidence/baseline-a5eafa9-receipt.json)

## Contratos de bits y modulación · WP-01 y WP-02

Se implementaron los contratos de bits, etiquetas, reloj e I/Q y las operaciones de mapeo y decisión para BPSK, QPSK, M-PSK y QAM cuadrada. La decisión emplea sectores o ejes de la grilla, con uso de memoria por bloque. Las pruebas comparan la geometría, la energía y las decisiones con referencias independientes y verifican relleno, reloj, casos extremos, cancelación y cambios de entrada. `python -B -X utf8 -m unittest discover -s tests -p test_communications_modulation.py` aprobó 12 pruebas. La medición focal en Windows cubrió 362/362 líneas y 117/118 ramas de los dos módulos, y la verificación estática aprobó 392 archivos. [Contratos y ejemplo](SCIENTIFIC_CONTRACTS.md#bits-reloj-y-constelaciones-en-python)

## Pulsos y filtrado · WP-03

Se incorporaron pulsos rectangular, RC y RRC, sobremuestreo por inserción de ceros, FIR de longitud completa y filtro adaptado. RC cancela la singularidad con una identidad de sinc. RRC factoriza el cero del numerador antes de dividir en la vecindad del polo. En los 79 valores de referencia, el mayor error absoluto medido fue 2,23 × 10⁻¹⁶. Los retardos de medio índice de FIR pares se conservan y su suma TX/RX da un índice entero. La publicación del resultado recalcula su huella después de añadir el reloj y la descripción del pulso.

Pasaron 19 pruebas mediante `python -B -X utf8 -m unittest discover -s tests -p "test_communications*.py"`. Se verificaron DTFT directa de coeficientes, convolución, ISI por suma de productos, compatibilidad con Project, cancelación y rechazo por memoria. La cobertura focal de los tres módulos fue 551/551 líneas y 159/160 ramas en Windows. La verificación estática aprobó 393 archivos. [Convenciones de pulsos](MATHEMATICAL_FOUNDATIONS.md#pulsos-y-retardo) · [Medición inicial](PERFORMANCE_REPORT.md)

## Canal y recepción · WP-04

Se implementó AWGN por SNR, Es/N₀ o Eb/N₀, con referencias separadas y varianza real o compleja. Se contrastaron las varianzas con intervalos χ² sobre 150 000 muestras y se observó la covarianza I/Q. La recepción recuperó QPSK sin ruido con retardo conocido, distinguió la corrección manual y estimó un desplazamiento y una fase inyectados con piloto. El cómputo escala cada ventana por separado para que un pico lejano no oculte un piloto débil. Se verificaron ambigüedad, señales cortas, cancelación, reloj y publicación con padres. Pasaron 32 pruebas focales. La medición de los cinco módulos cubrió 870/871 líneas y 244/246 ramas en Windows. [Contratos y criterios](SCIENTIFIC_CONTRACTS.md#canal-y-alineación) · [Perfiles de búsqueda](PERFORMANCE_REPORT.md)
