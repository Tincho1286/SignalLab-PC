# Consistencia de las interfaces

| Operación | Qt | Python | CLI | Publicación del Core |
| --- | --- | --- | --- | --- |
| DFT | Frontera compartida | `calculate_dft` | `dft` | `store_dft` |
| IDFT, FIR, cambio de tasa y PSD | Herramientas existentes | `dsp_application` | `dsp` | `store_signal` y `store_fir_design` |
| Flujo DSP | Disponible desde API y terminal | `run_pipeline` | `dsp-pipeline` | `store_pipeline` |

La DFT es la integración Qt del piloto. Los otros paneles Qt conservan sus motores y rutas históricas. Los contratos de `dft_application`, `dsp_application` y `dsp_pipeline` son experimentales. Las funciones auxiliares de sellado y el formato interno de verificación están sujetos a evolución documentada.
