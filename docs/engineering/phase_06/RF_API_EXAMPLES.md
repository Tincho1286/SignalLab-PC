# Ejemplos RF con Python y consola

## Cambiar la referencia de una red Touchstone

```python
from signallab_pc.rf_application import RFRequest, run_rf, store_rf
from signallab_pc.project import Project
from signallab_pc.touchstone import read_touchstone, write_touchstone

source = read_touchstone("medicion.s2p")
specification = RFRequest("renormalize", {"reference_ohm": [50, 75]})
result = run_rf(specification, (source,))
project = Project()
receipt = store_rf(project, result)
write_touchstone("medicion-renormalizada.ts", result.network)
```

La misma operación está disponible en **Redes multipuerto → Cambiar referencias**. La consola recibe este documento en `cambiar.json`.

```json
{
  "schema": 1,
  "operation": "renormalize",
  "parameters": {"reference_ohm": [50, 75]}
}
```

```text
python -m signallab_pc rf --request cambiar.json --network medicion.s2p --output calculo.slproj
```

La salida de consola indica los identificadores de la red, los orígenes y el informe. Una segunda operación puede usar `--source-session calculo.slproj --record-id ID` y guardar en otro archivo. Las solicitudes complejas usan pares `[parte_real, parte_imaginaria]` en `value_pairs`, `load_ohm_pairs` o `reflection_pairs`. Las entradas de matrices siguen el orden `[frecuencia, salida, entrada, 2]`.

## Evaluar una banda de Fourier con origen distinto de cero

```python
from signallab_pc.advanced_fourier import zoom_fft
from signallab_pc.model import Signal

record = Signal([1, -2, 0.5j, 2], origin=-2, metadata={"sample_rate_hz": 48000})
analysis = zoom_fft(record, -500, 2500, 401, units="Hz")
print(analysis.spectrum.axis[0], analysis.grid_step, analysis.nominal_dft_spacing)
```

El eje tiene paso de 7,5 Hz. La separación de una DFT de cuatro muestras es 12 000 Hz. Los 401 puntos permiten inspeccionar la curva del registro de cuatro muestras en la banda elegida.

## Reproducir los seis demostradores

```text
python -m tools.rf_demonstrators --output work/rf-examples
```

Cada informe lista los valores numéricos, la referencia independiente y la tolerancia. El demostrador F genera una red de prueba y un proyecto SLPROJ que se puede reabrir desde el Workbench.
