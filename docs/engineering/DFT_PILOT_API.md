# API de la DFT

`signallab_pc.dft_application` ejecuta la misma DFT que usa el escritorio. El flujo funciona en un proceso sin pantalla y las pruebas bloquean cualquier intento de importar un enlace de Qt. Los ejemplos usan el CPython fijado en `.python-version` y las dependencias científicas del proyecto.

| Contrato | Qué contiene |
| --- | --- |
| `DFTRequest` | Un `Signal` discreto, `length` opcional, `centered` y `phase_reference`. Por defecto toma la longitud de la señal y centra los bins con fase referida al índice real. |
| `DFTExecution` | Tope opcional de memoria estimada en bytes, plazo absoluto de `time.monotonic()`, un `threading.Event` de cancelación y una función opcional de progreso. |
| `DFTResult` | `spectrum`, un `Signal` que acepta la IDFT existente, la procedencia tipada y la estimación de memoria. |
| `DFTProvenance` | Longitud efectiva, tamaño y origen de la entrada, unidades del eje, reloj disponible, orden y referencia de fase. Persiste en `spectrum.metadata['dft_provenance']` con esquema 1. |

Con `sample_indices` se usa el índice entero original `n` en el exponente. Con `record_offset` se numera el dato inicial como `m=0`. La DFT directa es no normalizada. Si `N` es menor que la entrada, conserva las primeras `N` muestras. Si es mayor, agrega ceros. El orden centrado representa los bins desde `-floor(N/2)` en rad/muestra. Con `centered=False` el eje usa los índices `k=0…N−1`. La IDFT divide por `N` y puede restaurar el origen y el reloj. El argumento por defecto de la función numérica histórica `operations.dft` sigue usando `record_offset`. [Convenciones matemáticas](MATHEMATICAL_CONVENTIONS.md)

## Python

Desde la raíz del repositorio, ejecutar este ejemplo en Python. Produce una sesión que abre el escritorio y una señal JSON para la CLI.

```python
from time import monotonic
from threading import Event

from signallab_pc import session
from signallab_pc.dft_application import DFTExecution, DFTRequest, calculate_dft, store_dft
from signallab_pc.model import Signal
from signallab_pc.operations import idft
from signallab_pc.project import Project
from signallab_pc.storage import save_json

x = Signal([1 + 2j, -3, 0.5j], origin=-2,
           metadata={'sample_rate_hz': 4, 'time_start_s': -0.375})
cancel = Event()
execution = DFTExecution(max_work_bytes=4096, deadline=monotonic() + 10, cancel=cancel)
result = calculate_dft(DFTRequest(x, length=4), execution)
restored = idft(result.spectrum, restore_origin=True)
print(restored.axis.tolist(), restored.values.round(12).tolist())

project = Project()
source_id, result_id = store_dft(project, result, source=x, execution=execution)
session.save('python-dft.json', project, session.empty_workspace(),
             before_commit=execution.checkpoint)
save_json(x, 'input-dft.json')
print(source_id, result_id)
```

Al reutilizar una señal que ya está en el proyecto, pasar `source_id` en lugar de `source`. El ID es el del registro con el que se armó la solicitud. Al publicar una señal nueva y su resultado, ambos registros entran juntos. Mantener estables las muestras y metadatos del `Signal` mientras se ejecuta la operación. `Project` guarda instantáneas en el momento de publicar.

## CLI

```sh
python -m signallab_pc dft --signal input-dft.json --output cli-dft.json --length 4
python -m signallab_pc dft --session python-dft.json --record ID_DE_LA_SENAL --output ampliada.json --order bins --phase-reference record_offset
python -m signallab_pc dft --help
```

Usar el `source_id` que imprimió el ejemplo Python en lugar de `ID_DE_LA_SENAL`. La CLI devuelve en stdout un JSON con los IDs, la longitud efectiva y la estimación de memoria. Con `--session` conserva los resultados y el escritorio del archivo de entrada. `--timeout` recibe segundos. `--max-work-bytes` recibe bytes. Una ejecución cancelada con Ctrl+C devuelve 130. Los fallos de cálculo o escritura devuelven 1. Los errores de argumentos devuelven 2.

## Límites y entrega

La estimación del motor es `128 × N` bytes. El tope explícito puede reducir el límite de la aplicación. El motor mantiene su guarda dinámica basada en la RAM libre. La estimación se refiere al cálculo e incluye sus temporales estimados. La carga y serialización del proyecto pueden tener otro pico de memoria.

El progreso informa 0 al iniciar y 100 al completar el cálculo. La aceptación comprueba de nuevo cancelación y plazo antes de entregar el resultado. Si se pide cancelar durante una FFT, se descarta su salida cuando vuelve el control al proceso Python. Las API de sesión y proyecto comprueban el plazo o la cancelación antes de cambiar el estado. Una solicitud posterior a ese punto corresponde a una operación ya comprometida. Para coordinar varios procesos, asignar un escritor por archivo de destino. [Consideraciones de la Fase 01](PHASE_01_CLOSEOUT.md)
