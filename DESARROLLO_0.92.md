# SignalLab PC 0.92 — biblioteca común de resultados

28/10/2026. Se atiende la aclaración del usuario: los resultados deben reunirse en la biblioteca, no limitarse a un envío de transformadas al análisis de H.

## Registro de salidas

La ejecución común de cálculos registra las salidas principales y secundarias. Las señales, transferencias y modelos de estados conservan su tipo. Si un panel sólo hubiera publicado la primera parte de un resultado compuesto, se incorporan las demás salidas tipadas. Las tablas y datos complementarios se conservan completos junto al informe, con forma, tipo y valores; los no finitos se identifican explícitamente, sin convertirlos en cero. Los resultados ya registrados por un panel no se duplican por identidad.

Los informes publicados durante un cálculo incorporan su carga de datos antes de registrarse. La actualización de la biblioteca se agrupa al finalizar la recepción, en lugar de volver a dibujarla por cada salida. Cada entrada conserva la herramienta original incluso si se cambia de documento mientras el cálculo está en curso. Una cancelación o un error del motor no se presenta como un resultado terminado.

## CAS y expresiones

Cada celda válida del CAS se registra con su valor exacto completo, texto, presentación, supuestos y entrada original. No se copia todo el entorno de variables, funciones e historial. Una matriz o lista conserva el valor completo aunque su vista matemática sea parcial. Al recuperarla en CAS se restaura ese valor, sin depender de volver a interpretar su texto impreso.

Las transformadas ya se publicaban como cálculos, pero la biblioteca no permitía reutilizarlas como expresiones. Ahora tienen filtro Expresiones y destinos según su variable: CAS, transformada directa/inversa, creación de señal, medidas o análisis como H cuando corresponde. La conversión a H es una opción, no una condición para recuperar el resultado. Se mantienen las condiciones y las relaciones de origen. Las entradas de transformadas incluyen una parte de su definición para distinguir cálculos repetidos.

## Biblioteca

Todos los tipos se pueden abrir para consultar el valor conservado. Las expresiones se ven con notación matemática; los resultados CAS comparten la misma presentación vectorial que la hoja. Se indica la herramienta de origen y los resultados vinculados. Los destinos tipados incluyen las variantes compatibles dentro de cada problema, por ejemplo los distintos estudios de estados.

La barra se organiza en dos filas compactas, conservando guardar/abrir sesión dentro de Sesión. La exportación de un cálculo incluye los registros de los que depende, para que sus referencias a señales/modelos/tablas no queden sin datos. Se conserva compatibilidad con registros anteriores sin la nueva información de origen.

## Comprobación puntual

Se realizó un recorrido focalizado: CAS escalar/matriz, recuperación exacta de la matriz, Z directa/inversa y su relación de origen, creación de señal desde la expresión recuperada, captura automática de una salida secundaria y una tabla con NaN/infinito, filtro Expresiones y exportación con dependencias. No se recorrieron todos los menús ni se ejecutó la batería general, según el pedido del usuario.

Se mantiene abierta la consolidación hacia 1.0 y la revisión general de uso queda a cargo del usuario. El registro común no amplía por sí mismo el alcance matemático de cada operación.
