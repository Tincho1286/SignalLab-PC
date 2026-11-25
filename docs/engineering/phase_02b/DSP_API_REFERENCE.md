# Referencia DSP

Las operaciones en `signallab_pc.dsp_application` reciben una solicitud tipada y aceptan un `ExecutionContext` opcional. `calculate_idft`, `apply_fir` y `estimate_psd` devuelven un `Signal`. `resample` devuelve un resultado con señal y, si fue solicitado, filtro antialias y diagnóstico. `design_fir` devuelve un modelo digital y una especificación. `store_signal` usa `Project` para registrar dependencias. `store_fir_design` registra el modelo y sus especificaciones juntas.

[Ejemplos numéricos](operations/DSP_MATHEMATICAL_VALIDATION.md) · [Contratos matemáticos](operations/DSP_OPERATION_CONTRACTS.md)
