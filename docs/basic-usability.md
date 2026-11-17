# Cargar, editar y combinar muestras

Las herramientas básicas permiten preparar datos y obtener salidas independientes sin construir primero un proyecto. Cada entrada conserva sus fórmulas, muestras y último archivo o resultado. Los cuatro métodos de carga se distribuyen en dos filas para mantener visibles sus nombres en paneles estrechos.

## Pegar datos

En **Muestras → Pegar datos…**, la vista previa indica qué contiene cada columna. Se admite una secuencia horizontal o vertical, una tabla de eje y valor, partes real e imaginaria, o eje/real/imaginaria. Un encabezado se omite sólo al indicarlo. La coma decimal se activa explícitamente y requiere tabulaciones o punto y coma para separar columnas.

Las celdas pueden contener constantes y expresiones escalares como pi, 10^(-3) o 1+2i. Los datos se validan completos antes de reemplazar la lista editable. Una celda vacía no se convierte en cero. El eje debe ser uniforme y creciente; en discreto usa índices enteros consecutivos. No se ordenan ni remuestrean tablas irregulares.

## Editar y extraer

**Tabla y edición de muestras** conserva un historial de valores, nombre y eje. Deshacer y Rehacer modifican la edición actual. Aplicar edición publica una copia independiente; deshacer después de aplicar deja cambios pendientes y mantiene intacta aquella salida. Abrir otro registro inicia un historial nuevo.

Pegar muestras reemplaza un bloque del registro como una sola acción reversible. Debe conservar el paso y quedar dentro de sus límites; un pegado inválido no modifica parte de la tabla. Extraer tramo recibe dos coordenadas incluidas y crea una señal con los valores de la edición actual. No aplica el resto del registro. Conserva los índices y el reloj físico; los límites continuos deben coincidir con puntos existentes.

## Combinar y leer los valores

En **Sumar o multiplicar señales**, Intercambiar entradas mueve ambas definiciones completas sin calcular. La suma abarca la unión de los registros; el producto conserva el intervalo de la nueva primera señal. Cada entrada vale cero fuera de su registro.

La pestaña **Operación por muestra** acompaña al informe. Muestra x, la segunda entrada, el resultado y qué registros cubren cada coordenada. Sus páginas y su exportación CSV conservan el último cálculo, aunque se editen las entradas. En continuo usa la misma interpolación lineal que la operación; no convierte impulsos Dirac en muestras finitas. Ir a selecciona el punto de salida más próximo en continuo, o un índice entero en discreto.

Estas mejoras pertenecen a la 1.8.14 preliminar. Las figuras y acciones de reutilización siguen junto a los resultados.
