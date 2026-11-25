# Catálogo de oráculos

| Familia | Referencia independiente | Pruebas |
| --- | --- | --- |
| DFT, IDFT y DTFT | Suma de exponenciales complejas, inversa y Parseval | `test_math_contracts.FourierContracts`, `test_math_dft_pilot` |
| Fourier y series | Integrales analíticas, desplazamiento de Dirac, peso en extremos | `test_math_sampling_fourier.FourierReferences`, `test_symbolic_fourier` |
| Laplace, Z, ROC y energía | Pares conocidos, series geométricas, ortogonalidad y polos repetidos | `test_algebra_reference`, `test_algebra_support`, `test_math_reliability` |
| Señales, convolución, correlación | Sumas directas y conjugación por definición | `test_math_contracts.SignalContracts` |
| Muestreo, reconstrucción y cuantización | Exponencial analítica, suma del FIR de conversión, niveles y error de referencia | `test_math_sampling_fourier.SamplingReferences` |
| FIR, IIR y LTI | Retardos, recursión con historia, fórmula y raíces independientes | `test_math_contracts.SystemContracts`, `test_math_expression_systems`, `test_math_dsp_pipeline` |
| PSD | Sumas DFT directas, balance de potencia y tono de Nyquist a escala extrema | `test_math_sampling_fourier.FourierReferences`, `test_math_dsp_application` |
| Espacio de estados | Recurrencia y exponencial escalar | `test_math_contracts.StateContracts` |
| CAS y aritmética | Igualdad simbólica, sustitución, ramas y operaciones exactas | `test_cas_worksheet`, `test_cas_assumptions`, `test_math_contracts.ScalarContracts` |
