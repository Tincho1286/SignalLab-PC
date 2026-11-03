# SignalLab PC 0.69 — documentos independientes y continuidad de datos

## Un documento por problema

La organización pública mantiene 33 herramientas y sus 72 variantes. Hasta 0.68, varias herramientas públicas distintas terminaban en un mismo contenedor heredado: por ejemplo, crear, editar, transformar y sumar señales compartían una pestaña; los distintos problemas de sistemas y filtros también compartían otra.

El escritorio ahora asigna un documento a cada problema público. Crear una señal, transformarla, analizar un sistema y obtener su respuesta temporal pueden permanecer abiertos simultáneamente. Sus entradas y resultados se conservan al cambiar de pestaña. Las variantes del mismo problema —por ejemplo DFT/DTFT dentro de Fourier, o convolución lineal/circular— permanecen en un solo documento. Cerrar una pestaña mantiene los datos durante la ejecución, como indicaba el comportamiento anterior.

El escritorio construye directamente la página elegida, sin abrir previamente una herramienta de otro problema como paso interno. Se mantienen las rutas anteriores de envío y de ayuda. Las figuras conservan su ventana independiente al cambiar de documento.

## Correcciones de datos

- Una fórmula nueva tiene prioridad sobre una realización importada anterior al cambiar de variante. Antes, la conservación de coeficientes/SOS podía restablecer el modo Coeficientes aunque se hubiese escrito otra H.
- Una entrada de importación vacía deja vacío el destino compatible: no recupera silenciosamente el archivo que esa vista había utilizado antes.
- Los coeficientes de series muestran c[k], el primer armónico k₀ y la cantidad de coeficientes. El cálculo finito admite k en expresiones, conservando n por compatibilidad. Las vistas de síntesis y de muestras temporales cambian las etiquetas según el dato esperado.

## Evidencia dirigida

Se abrieron las 33 herramientas públicas y se verificó un documento y una acción de cálculo por problema. Se comprobaron documentos distintos para creación/transformación, análisis/respuesta temporal y diseño FIR/IIR; mismo documento para las variantes de transformación, convolución y Laplace. Se conservó el resultado de generación al cambiar de documento y se comprobó que su figura continuaba abierta.

Se calculó convolución/cambio de método conservando entradas e índices; se envió una transferencia por la ruta heredada de respuesta en frecuencia, se analizó y se verificó su respuesta. Su envío a respuesta temporal abrió otro documento y permitió volver al análisis con el resultado intacto. Se consultó su plano de polos y ceros. Las rutas heredadas de Laplace/Z y la ayuda contextual conservaron el modo correspondiente.

Los casos específicos de copia verificaron una fórmula nueva tras importar un sistema y una entrada importada vacía frente a un archivo antiguo. Para c[k]=1/(1+k²), k=-1,0,1 y T=2π, se obtuvieron líneas en -1,0,1 rad/s con pesos 2π·[1/4,1,1/4] y potencia 1.5. Se comprobó el cambio de etiquetas entre análisis y síntesis de series. Revisión de ancho a 800×600 en generación: sin desplazamiento horizontal del documento.

## Continuación hacia la primera estable

La independencia de documentos y los problemas de copia identificados quedan resueltos en los recorridos anteriores. Siguen pendientes los cierres dirigidos de cálculo y convenciones de CIERRE_1.0.md. También corresponde normalizar los informes que todavía recurren a campos internos/JSON para que su lectura resulte coherente con las vistas matemáticas. No se declara la aplicación estable por esta reorganización.
