# Registro de Fase 03

## 26 de noviembre de 2026 · WP-00

Se consolidó la documentación de 02C y se despachó la matriz única de Windows y Linux para `a5eafa9a1e98116e84b57d3bb0e8881ea02b2931`. El candidato incorpora el cierre de E-01, las aprobaciones E-02, E-03 y E-05, y E-04 en seguimiento. La auditoría de arquitectura identificó los servicios DSP, el contexto y pool de ejecución, los formatos y el patrón de campaña que se reutilizan. [Matriz](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45812233593) · [Arquitectura](ARCHITECTURE.md)

Se fijaron convenciones de rotación, energía, ruido, reloj y métricas. Se generaron vectores por cuadratura, reflexión binaria y suma directa y se contrastó su alcance con Komm 0.37.0. El empaquetado conserva el lock del Core durante la apertura de fase. [Auditoría matemática](MATHEMATICAL_AUDIT.md) · [Dependencias y referencias](INTEGRATION_CATALOG.md)

Se ejecutaron DFT, IDFT y FIR en CPython 3.14.10 con la importación de Qt bloqueada. El retorno DFT/IDFT conservó muestras, origen, reloj y unidades. El FIR de longitud completa conservó la cola y el reloj. Se ensayó SLPROJ con seis registros sintéticos del tamaño de una corrida de comunicaciones y se verificó la reapertura. `python -B -X utf8 tools/check_static.py` aprobó 390 archivos. [Perfiles y tamaños](PERFORMANCE_REPORT.md)
