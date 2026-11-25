# Demostrador DSP

```python
from signallab_pc.dsp_application import ResampleRequest
from signallab_pc.dsp_pipeline import DSPPipelineRequest, run_pipeline
from signallab_pc.filters import Transfer
from signallab_pc.model import Signal

x = Signal([1, 2, -1, 0, 1, 0], -2, metadata={'sample_rate_hz': 12})
flow = DSPPipelineRequest(ResampleRequest(x, 2, 3), Transfer([.25,.5,.25],[1]),
                          psd_method='periodogram', psd_window='boxcar')
out = run_pipeline(flow)
print(out.filtered.metadata['sample_rate_hz'], out.dft.spectrum.values, out.psd.values)
```

En la GUI se emplean Cambio racional de tasa, aplicación del FIR, DFT y PSD. La salida filtrada es el origen de ambos análisis. Desde CLI, exportar la entrada como JSON de señal y usar `python -m signallab_pc dsp-pipeline --signal entrada.json --output flujo.json --up 2 --down 3 --fir .25 .5 .25 --psd-method periodogram --window boxcar`. La sesión resultante puede abrirse en el escritorio.
