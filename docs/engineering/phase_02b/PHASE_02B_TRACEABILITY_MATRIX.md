# Trazabilidad de Fase 02B

| Requisito | Decisión y código | Prueba y evidencia | Estado |
| --- | --- | --- | --- |
| CORE-00 | Verificar el piloto y reutilizar evidencia del SHA con el mismo árbol de código. | [Línea base](PHASE_02B_BASELINE.md) | Verificado |
| CORE-01 | [ADR 002](architecture/ADR-002-COMMON-CONTRACTS.md) | 2 pruebas de ejecución y 6 del piloto en Windows | Verificado |
| CORE-02 | [Contratos DSP](operations/DSP_OPERATION_CONTRACTS.md) | [Oráculos](operations/DSP_MATHEMATICAL_VALIDATION.md) | Verificado |
| CORE-03 | [Arquitectura del flujo](pipelines/DSP_PIPELINE_ARCHITECTURE.md) | `test_math_dsp_pipeline.py` · 3 pruebas en Windows | Verificado |
| CORE-04 | [ADR 003](architecture/ADR-003-SCIENTIFIC-STORAGE.md) · [Benchmark](storage/STORAGE_BENCHMARK_REPORT.md) | 48 combinaciones y 4 pruebas locales | Verificado parcialmente |
| CORE-05 | Guardas por etapa y pruebas de interrupción. | Pendiente | Propuesto |
| CORE-06 | API experimental y ejemplos sin dependencias de interfaz. | Pendiente | Propuesto |
| CORE-07 | Matriz multiplataforma reproducible. | Pendiente | Propuesto |
