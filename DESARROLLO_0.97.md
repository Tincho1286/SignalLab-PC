# SignalLab PC 0.97 — resultados de estados reutilizables

28/10/2026. Se completa el recorrido entre los estudios de Espacio de estados y el análisis de transferencias, dentro de las herramientas existentes. Se conservan 32 problemas y 76 variantes.

## Transferencia útil desde el resultado

Obtener transferencia muestra primero H(s) o H(z) en formato matemático, después el canal y el resto de datos. Los selectores de entrada y salida están antes de las tablas de matrices para que no queden debajo de un editor grande.

El resultado incorpora Analizar (polos/ceros, frecuencia o temporal), Usar filtro en y Exportar filtro. Estas acciones usan la transferencia calculada y registrada, sin exigir buscarla en la biblioteca ni copiar coeficientes. El informe identifica el par entrada/salida y el período del modelo discreto. La transferencia supone estado inicial nulo y puede ocultar modos internos no controlables u observables. Sus coeficientes son numéricos; no se eliminan residuos mediante una tolerancia arbitraria.

## Modelos reutilizables

Estructura, simulación, frecuencia y discretización ofrecen Usar modelo calculado en. Se copian matrices, dominio, nombre y T al estudio elegido, sin recalcularlo automáticamente. El modelo discreto obtenido puede pasar directamente a simulación, frecuencia, estructura o transferencia. La entrada continua original conserva su borrador para comparar otro método o período. Los modelos discretos no se ofrecen como entrada de Discretizar.

Modificar los campos no reemplaza el resultado. El indicador de datos modificados conserva su significado y las acciones siguen usando el último cálculo. El envío desde la biblioteca y desde el diagrama de realización utiliza el mismo camino común de carga.

## Exportación y carga

Exportar modelo guarda el registro nativo SignalLab con sus dependencias. Cargar modelo permite elegir un resultado de la biblioteca o abrir ese JSON desde el propio panel. Si el archivo contiene varios modelos, el selector identifica nombre, dominio, T y dimensiones, con el último modelo como propuesta. La opción de discretización sólo ofrece modelos continuos.

El JSON conserva coeficientes complejos y sus matrices completas. Las vistas abreviadas de las tablas o informes no recortan esos datos. Se mantienen los nombres de los modelos al reutilizarlos y recalcularlos.

## Presentación y documentación

El informe de estructura adopta el formato de lectura común, con rangos, estabilidad y explicaciones conectadas. Se actualizan las ayudas de transferencia y discretización para reflejar los controles disponibles. La matriz vigente de Sistemas I/II deja de indicar como ausentes capacidades de reconstrucción discreta, aritmética finita y reutilización de estados ya implementadas; conserva sus límites reales.

## Comprobación focalizada

Se recorrió discretizar un modelo RC, cambiar después el período de entrada y reutilizar el resultado anterior en simulación, verificando matrices y T conservados. Se comprobó exportación/apertura JSON nativa, transferencia del canal frente a su respuesta analítica y envío directo al análisis de H(z). No se ejecutó una batería general ni una campaña de resoluciones.

La compilación sigue siendo de desarrollo; esta mejora no demuestra por sí sola que el objetivo de 1.0 esté terminado.
