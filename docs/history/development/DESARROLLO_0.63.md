# SignalLab PC 0.63 — coherencia de ejes conjuntos

- Análisis ampliado de Fourier: los cuatro subgráficos comparten ahora el eje horizontal, incluidos límites, marcas y zoom. Antes podían tomar límites independientes.
- Ventanas y FFT: DFT, DTFT y referencia fijada usan los límites de sus coordenadas completas, sin depender de la curva seleccionada ni de los puntos con fase definida. Se preservan las frecuencias originales; no se interpola la DFT para forzar coincidencias.
- Resultados superpuestos: se rechazan ejes con dominio o unidades incompatibles antes de mostrarlos juntos.
- El análisis ampliado también respeta el carácter discreto de densidades derivadas y cortes FFT.

Revisión de las rutas gráficas conjuntas del código:
- Fourier simple/ampliado, DFT-DTFT, ventanas y referencias: correcciones anteriores y comprobaciones dirigidas.
- Familias de filtros digitales/analógicos y especificaciones: una misma rejilla de frecuencia para todos los sistemas; subgráficos con X compartida.
- Respuesta de sistemas y análisis algebraico-numérico: módulo/fase/dB con X compartida.
- Señales conjuntas, partes par/impar y vistas previas: cada señal conserva su origen, con X compartida entre componentes y validación de unidades.
- Espacio de estados multicanal: todos los canales reciben las mismas coordenadas temporales/frecuenciales; X compartida entre componentes.
- Aliasing: curvas y muestras se expresan en t·Fs sobre un mismo eje.
- Polos y ceros: plano complejo común y proporción igual entre parte real e imaginaria.
- Espectrograma e histogramas: un solo sistema de coordenadas, sin superposición de ejes independientes.

No se igualan escalas verticales de magnitudes diferentes: módulo, dB, fase y retardo tienen unidades distintas. Las curvas dentro de cada subgráfico sí comparten su escala vertical.

Comprobación puntual: DFT contra suma directa de una señal compleja con origen negativo, intervalo de varios períodos, tres vistas Fourier y zoom; FFT impar, referencia fijada, selección DFT/DTFT, módulo/fase y real/imaginaria; rechazo de ejes incompatibles. La revisión de las otras familias es de sus rutas de trazado, no una campaña exhaustiva de pruebas de interfaz.
