# SignalLab 0.56 · Muestreo pasabanda

Nueva herramienta independiente en Muestreo y reconstrucción. Recibe los bordes positivos de una señal real en rad/s y calcula los intervalos de frecuencias angulares de muestreo que evitan superposición espectral. La tasa candidata es opcional.

- Distingue interior con margen, contacto teórico y solapamiento.
- Informa Ωs, Fs en muestras/s y T; conserva las frecuencias de entrada en radianes.
- Gráfica de intervalos, informe con formato y ayuda ilustrada en colores.
- CSV con todos los intervalos. La gráfica muestra hasta 40 y el informe hasta 100 para mantenerse legibles; estos límites no recortan el cálculo ni la exportación.
- Una tasa válida se puede enviar a Muestrear una expresión. Sólo copia Fs: no cambia la señal ni calcula automáticamente.
- Las bandas de guarda de filtros reales y las componentes impulsivas en bordes requieren cuidado; los contactos no se presentan como reconstrucción garantizada.

Comprobación acotada: intervalos conocidos, tasa interior, contacto, solapamiento, CSV, apertura del panel y ayuda. No se repite la validación general del portable.

Fundamento: intervalos del teorema de muestreo pasabanda, descritos en el teorema 1 de https://pmc.ncbi.nlm.nih.gov/articles/PMC5855515/ . No se implementan ejercicios particulares.

## Avance de alcance

Queda cubierto el punto de selección de tasas de muestreo pasabanda de COBERTURA_SYS_I_II_0.54.md. El diseño analógico por especificaciones se agregó en 0.55. Siguen pendientes diagramas de realización, ampliaciones de módulo–fase, modulación y demodulación, transformadas bilaterales/ROC y aritmética de implementación. La síntesis física de filtros también queda pendiente. No se amplía Señales Aleatorias. Esta versión sigue siendo preliminar.
