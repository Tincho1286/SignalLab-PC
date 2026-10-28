# SignalLab PC — ampliación 0.22

## Implementado en código
- Menú Señales aleatorias: generación gaussiana, uniforme y Bernoulli con semilla PCG64 reproducible.
- Estadísticas de registros reales o complejos: media, varianza con divisores N y N−1, valor cuadrático medio y RMS.
- Histograma de parte real, imaginaria o módulo, con densidad por intervalos.
- Integración con reutilización, exportación y biblioteca de ayuda.

No se ejecutaron pruebas ni diagnósticos. Las propiedades de un registro finito no se presentan como pruebas de estacionariedad, ergodicidad o distribución.

## Alcance de trabajo siguiente
- Procesos aleatorios: conjuntos de realizaciones, estimación de correlación y covarianza, relación entre autocorrelación y densidad espectral.
- DSP: análisis tiempo-frecuencia y diseño de filtros por especificaciones.
- Sistemas y señales: revisar la cobertura de transformadas, respuesta y estabilidad frente a un temario explícito.
- Usabilidad: mantener entradas independientes, salidas inmediatamente visibles y ayuda por herramienta.

## Referencia curricular
MIT OpenCourseWare, Signals, Systems and Inference (6.011): https://ocw.mit.edu/courses/6-011-signals-systems-and-inference-spring-2018/
MIT, lecturas de Signal Processing: Continuous and Discrete; incluye Oppenheim y Schafer, y Proakis y Manolakis: https://ocw.mit.edu/courses/2-161-signal-processing-continuous-and-discrete-fall-2008/pages/readings/
Estas referencias orientan la cobertura; no se afirma equivalencia completa con un libro o asignatura.
