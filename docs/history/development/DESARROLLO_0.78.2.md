# SignalLab PC 0.78.2 · raíces visibles en el origen

27/10/2026. Corrección de representación de polos y ceros en cero, aplicada a todas las vistas públicas de raíces.

## Cambio

Los casos de reproducción contenían raíces en cero en los datos del gráfico, pero sus marcas pequeñas podían confundirse con los ejes o quedar superpuestas. Ahora se dibujan por encima de los ejes y de la rejilla. Los ceros tienen un círculo con fondo del plano y los polos una cruz de tamaño distinguible; cuando coinciden se ven ambos símbolos en la misma coordenada.

La leyenda indica cuántos ceros y polos coinciden exactamente en el origen. Esa información queda fuera del área de datos, junto con las referencias de los símbolos. La consulta también lo indica en su informe. En polar, módulo cero está en el centro; no se atribuye un ángulo matemático definido al origen.

Se usa la misma representación en Polos y ceros de análisis, el editor de diseño, el dibujo de raíces de los paneles anteriores y los polos del análisis en espacio de estados. El cambio no agrega raíces, no elimina cancelaciones ni cambia el motor de raíces. Tampoco desplaza puntos a un epsilon para hacerlos visibles: cero permanece en cero, y las raíces cercanas mantienen sus valores.

## Comprobación dirigida

Se revisaron un cero digital en origen, un retardo con polo en origen, dos ceros y dos polos coincidentes y un sistema analógico con cero/polo en el origen. Se comprobó la vista cartesiana y la polar, las coordenadas de las marcas y su prioridad de dibujo, y se revisaron capturas.

Se recorrió también la entrada de fórmulas z y 1/z desde Analizar un sistema, el diseño con listas de ceros y polos en cero, el dibujo histórico y modelos de estados continuos y discretos con autovalor cero. Una raíz en 1e-12 permaneció distinta de cero. No se realizó una campaña general de pruebas del resto de las herramientas.

Se mantienen la UI oscura, la calculadora CAS y la corrección del informe de ajustar fase de 0.78.1. Los portables anteriores se conservan.
