# API experimental de Engineering Core

**Criterio previo de WP-02B.06.** La API de DFT debe conservarse, la CLI debe reutilizar carga, ejecución y guardado, y los ejemplos deben correr sin Qt. Las operaciones autorizadas se exponen en módulos sin dependencias de presentación.

| Módulo | Contrato |
| --- | --- |
| `dft_application` | `calculate_dft`, `DFTRequest`, `DFTResult`, `store_dft`. |
| `dsp_application` | IDFT, diseño y aplicación FIR, conversión racional y PSD. Solicitudes y procedencia específicas. |
| `dsp_pipeline` | `DSPPipelineRequest`, `run_pipeline`, `estimate_pipeline_memory` y `store_pipeline`. |
| `execution` | `ExecutionContext` y `ResourcePool`. `DFTExecution` sigue disponible. |
| `scientific_storage` | `save_binary_signal` y `load_binary_signal` para una señal opcional. |

`python -m signallab_pc dft --help`, `python -m signallab_pc dsp --help` y `python -m signallab_pc dsp-pipeline --help` muestran las entradas de consola. Todas usan los mismos controles de sesión, plazo y memoria estimada.
