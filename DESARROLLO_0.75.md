# SignalLab PC 0.75 · edición con salida directa

27/10/2026. Desarrollo hacia 1.0; se mantiene la organización y la apariencia de 0.74.

## Edición de muestras

La misma herramienta admite una secuencia discreta o un registro continuo muestreado. Sus entradas locales siguen disponibles por fórmula/tramos, lista, archivo o resultado. Al enviar una señal al editor desde otra herramienta se abre directamente en la tabla.

Abrir en tabla carga el registro de trabajo. Aplicar edición valida y aplica nombre, origen, paso y muestras en una sola acción. Se elimina la exigencia de aplicar el eje por separado y después guardar en el proyecto para poder recuperar la señal.

La pestaña Resultado contiene informe, valores, figura externa, exportación CSV/JSON y el menú común Usar en otra herramienta. No hace falta pasar por el panel de resultados de la sesión. El borrador y la salida aplicada son copias independientes: editar después de aplicar no cambia un resultado ya mostrado, exportado o enviado. Se avisa cuando hay cambios pendientes. Abrir otra entrada conserva primero el borrador pendiente como resultado; si no se puede aplicar, no reemplaza la tabla.

Los índices discretos son enteros con paso 1; los tiempos admiten origen real y paso positivo. Las etiquetas distinguen ambos casos. Las celdas Real e Imaginaria admiten expresiones constantes como pi, 1/3 y 10^(-3), usando el lector numérico existente. Se mantiene la paginación.

Al modificar muestras o eje se retira la expresión de origen como definición exacta y se conserva como referencia en los detalles. Cambiar sólo el nombre no invalida la fórmula. El editor trabaja con registros ordinarios: no modifica impulsos Dirac como alturas finitas ni convierte muestras continuas en una definición algebraica exacta.

## Adaptación de tamaño

La carga del editor y las pestañas comunes de resultado toman el tamaño de la página visible. Esto evita que una página de informe oculta conserve su ancho anterior y fuerce un desplazamiento horizontal al volver de otra herramienta. Se mantienen los controles y el desplazamiento vertical para ventanas pequeñas.

## Comprobación dirigida

Se recorrió la edición de tres muestras, con pi y una parte imaginaria 10^(-3), cambio conjunto de nombre/origen, salida enviada mediante el menú real a Fourier y cálculo en el destino. Se verificó que editar de nuevo conserve la salida anterior y que exportar CSV use esa salida aplicada. Se comprobó también un registro continuo con origen pi/10, paso 0.01 y una muestra 1/3, su exportación JSON, la conservación del original y el rechazo de índices fraccionarios o pasos negativos. Se revisó la paginación con 1002 muestras y el documento a 800×600 y 640×480, incluido el regreso desde Fourier que expuso la restricción de ancho corregida.

Esta revisión se limita al recorrido modificado. Las carencias académicas documentadas en COBERTURA_SYS_I_II_ACTUAL.md siguen abiertas; la versión no se declara 1.0 estable. Los portables anteriores se conservan.
