# Ejemplos de Engineering Core

Ejecutar `python -B tools/example_engineering_core.py work/ejemplos-core` desde el repositorio. El script genera una entrada real con reloj, aplica DFT e IDFT, diseña un FIR y lo aplica con cola, convierte la tasa, calcula PSD, ejecuta el flujo, guarda y reabre la sesión, comprueba la cancelación y hace un round trip binario. Los resultados reproducibles se pueden abrir en la GUI.

```powershell
python -m signallab_pc dft --signal work/ejemplos-core/entrada.json --output work/ejemplos-core/dft.json
python -m signallab_pc dsp resample --signal work/ejemplos-core/entrada.slbin --output work/ejemplos-core/convertida.json --up 2 --down 3
python -m signallab_pc dsp psd --signal work/ejemplos-core/entrada.json --output work/ejemplos-core/psd.json --method periodogram --window boxcar
python -m signallab_pc dsp fir-design --kind lowpass --taps 9 --f1 .18 --output work/ejemplos-core/fir.json
python -m signallab_pc dsp fir --signal work/ejemplos-core/entrada.json --output work/ejemplos-core/filtrada.json --coefficients .25 .5 .25
python -m signallab_pc dsp-pipeline --signal work/ejemplos-core/entrada.json --output work/ejemplos-core/flujo.json --up 2 --down 3 --fir .25 .5 .25 --psd-method periodogram
```

Para reconstruir una DFT mediante CLI, pasar su `result_id` a `dsp idft --session work/ejemplos-core/dft.json --record RESULT_ID --output work/ejemplos-core/inversa.json`. Las opciones de cada operación aparecen con `--help`.

En Jupyter con el repositorio como directorio de trabajo, usar el mismo ejemplo desde una celda. Jupyter se instala fuera del núcleo si el usuario quiere esa interfaz.

```python
from tools.example_engineering_core import demo

results = demo("work/ejemplos-notebook")
results["psd"].metadata["density_units"]
```
