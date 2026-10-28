# SignalLab PC 0.68 — una herramienta por problema

## Organización y datos

La 0.67 exponía 72 operaciones en el explorador y el catálogo. La 0.68 las conserva internamente y publica 33 herramientas. Convolución, correlación, energía/potencia, Fourier, series, espacio de estados, FIR, IIR, cambio de tasa y otros problemas reúnen sus variantes dentro de una misma página.

Los selectores sólo muestran opciones válidas para el dominio y el método actuales. Numérico significa evaluar un registro finito, cuyas muestras también pueden definirse por una fórmula; Algebraico trabaja sobre expresiones y sus condiciones. Se conserva el último método elegido al volver a una herramienta. La búsqueda específica sigue llegando a la variante solicitada, sin agregar entradas al menú.

Al cambiar de método se llevan las definiciones de entradas compatibles, sin evaluarlas ni publicar cálculos nuevos. Los modelos de estados conservan A, B, C, D, dominio y período entre estudios compatibles. No se copian muestras temporales como coeficientes de DFT inversa ni muestras de una serie como sus coeficientes. Tampoco se interpreta un modelo discreto como continuo para discretizarlo. Los cambios incompatibles conservan las entradas propias y muestran una explicación breve.

Los menús de reutilización también muestran un destino por herramienta, con una variante compatible con el resultado. Se mantienen las rutas anteriores para los envíos y la ayuda específica de cada cálculo. Las relaciones de frecuencia tienen su sección propia; no se presentan como un cambio de tasa de datos.

## Correcciones funcionales encontradas

El marcado de botones heredados podía conservar una acción anterior al cambiar el estudio. Se elimina ese marcado residual y la cabecera toma la acción del estudio activo. Se diferencia la acción principal de los botones secundarios, como superponer DFT y DTFT.

Los cambios entre obtener coeficientes y reconstruir series, y entre definir un RC y despejar un componente, perdían sus referencias a botones cuando los controles se trasladaban a la página independiente. Los callbacks ahora conservan las referencias. Las series continuas sólo habilitan sus acciones continuas y las discretas sus acciones discretas. Ecuaciones diferenciales incorpora la acción común de cálculo.

Las constantes de matrices pasan por el mismo parser seguro que los coeficientes de transferencias: pi, fracciones, potencias y complejos, en lugar de limitarse a literales de Python.

## Comprobaciones dirigidas

- Cobertura exacta: 33 herramientas, 72 variantes; apertura y acción de cálculo de todas las herramientas públicas.
- Cambio de convolución lineal a circular conservando ambas entradas y sus orígenes; ejecución de ambos cálculos; acceso al modelo continuo y algebraico.
- Copia de matrices y período entre análisis y frecuencia; cálculo; rechazo de una interpretación continua automática de un modelo discreto.
- Separación de la entrada temporal y los coeficientes de DFT inversa.
- Búsqueda de Fourier continua inversa algebraica, memoria del último método y ayuda contextual.
- Destinos de reutilización sin duplicados por variante.
- Acción principal real de DTFT, CTFT, inversa continua, series continuas/discretas, reconstrucción y EDO; cambio de síntesis y vuelta a análisis.
- Matriz con pi, 10^(-3), 1/2 y un coeficiente complejo.
- Capturas del catálogo de espectros y de Fourier a 800×600; sin desplazamiento horizontal del documento en ese caso.

## Continuación hacia 1.0

Esta entrega corrige organización y recorridos; no convierte por sí sola el proyecto en estable. Quedan los cierres dirigidos de convenciones, respuestas con condiciones iniciales, alcance de Laplace/Z y ayuda ya registrados en CIERRE_1.0.md. Hay que contrastar el comportamiento vigente antes de afirmar que esos recorridos están cerrados. No se repite una campaña matemática general por una modificación de navegación.
