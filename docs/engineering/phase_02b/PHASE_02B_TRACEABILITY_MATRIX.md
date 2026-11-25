# Trazabilidad de Fase 02B

| Requisito | Decisión y código | Prueba y evidencia | Estado |
| --- | --- | --- | --- |
| CORE-00 | Verificar el piloto y reutilizar evidencia del SHA con el mismo árbol de código. | [Línea base](PHASE_02B_BASELINE.md) | Verificado |
| CORE-01 | [ADR 002](architecture/ADR-002-COMMON-CONTRACTS.md) | 2 pruebas de ejecución y 6 del piloto en Windows | Verificado |
| CORE-02 | [Contratos DSP](operations/DSP_OPERATION_CONTRACTS.md) | [Oráculos](operations/DSP_MATHEMATICAL_VALIDATION.md) | Verificado |
| CORE-03 | [Arquitectura del flujo](pipelines/DSP_PIPELINE_ARCHITECTURE.md) | `test_math_dsp_pipeline.py` · 3 pruebas en Windows | Verificado |
| CORE-04 | [ADR 003](architecture/ADR-003-SCIENTIFIC-STORAGE.md) · [Benchmark](storage/STORAGE_BENCHMARK_REPORT.md) | 48 combinaciones por plataforma y 4 pruebas locales | Verificado |
| CORE-05 | [Política](contracts/RESOURCE_MANAGEMENT_POLICY.md) · [Límites](contracts/EXECUTION_LIMITS.md) | [Pruebas de robustez](validation/PIPELINE_ROBUSTNESS_REPORT.md) · 5 + 3 pruebas en Windows | Verificado |
| CORE-06 | [API](ENGINEERING_CORE_API.md) · [Guía](ENGINEERING_CORE_DEVELOPER_GUIDE.md) | [Ejemplos](ENGINEERING_CORE_EXAMPLES.md) y 2 pruebas headless | Verificado |
| CORE-07 | [Cierre](closeout/PHASE_02B_CLOSEOUT.md) | [Validación](validation/PHASE_02B_VALIDATION_REPORT.md) · [Resultados de CI](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45638606172) | Verificado |
