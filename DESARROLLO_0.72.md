# SignalLab PC 0.72 — transformadas claras y ayuda adaptable

## Uso de Laplace y Z

Directa, Inversa y, en Z, Muestras finitas conservan sus entradas y resultados por separado dentro del mismo documento. Cambiar de operación ya no interpreta la fórmula temporal como si fuese una expresión transformada. Volver a una operación recupera su resultado, con el estado actualizado o modificado correspondiente. La llegada de un cálculo mientras otra operación está activa conserva el resultado en su operación original sin reemplazar el informe visible.

La salida principal es Expresión y condiciones, con notación matemática y el alcance del cálculo. Una rama convergente de Z se muestra junto con su condición, sin presentar la suma pendiente fuera de esa rama como el resultado principal. Una transformada no resuelta se identifica expresamente. La inclusión de cero e infinito se distingue en registros finitos; los parámetros se conservan cuando impiden decidir esos extremos.

Copiar resultado a la inversa toma el último resultado calculado, sin ejecutar un nuevo cálculo. Las directas Z de soporte izquierdo sugieren la rama izquierda y conservan su condición como referencia; la ROC debe seguir siendo compatible para recuperar la misma señal. La inversa Z permite desactivar la generación del registro numérico. Primer índice y cantidad delimitan la tabla y la figura, no la fórmula completa. Las muestras, cuando existen, siguen siendo exportables y reutilizables.

## Correcciones de cálculo y entrada

- Laplace directa requiere x(t) y la inversa X(s). Se rechaza la variable de la otra operación en lugar de tratarla como parámetro constante y producir una fórmula engañosa. Z valida asimismo n frente a z y rechaza otras variables de eje reservadas.
- La selección de ROC por radio compara el radio con el módulo de los polos mediante constantes exactas. Se elimina la tolerancia absoluta que rechazaba regiones válidas cuando los radios eran menores que 1e-12. Un radio que coincide exactamente con un polo se rechaza. Si no puede decidirse la comparación simbólica, se pide concretar los parámetros.
- El campo de radio oculto no participa en los modos exterior/interior. Los campos de muestras ocultos no se exigen al obtener sólo la fórmula.
- Los informes distinguen Laplace unilateral de una transformada bilateral; una delta tiene convergencia en todo el plano finito. Dirac y los impulsos discretos usan notación delta en las fórmulas.

## Ayuda y pantallas pequeñas

La ayuda de Z incorpora un esquema en colores para comparar exterior, interior y anillo con la misma función racional. Explica que un radio interior elige una región y no fija sus bordes. Los parámetros y el procedimiento coinciden con los controles visibles. Se actualizó también la ayuda de aliasing a rad/s y la referencia a las cuatro fuentes de señal.

En ventanas estrechas, la biblioteca muestra el artículo a todo el ancho y permite abrir la lista con Buscar otro tema. Al elegir un tema, la lista vuelve a cerrarse. En ventanas amplias, índice y artículo permanecen lado a lado. Los datos de transformadas usan todo el ancho de su columna y se retiraron márgenes anidados que provocaban desplazamiento horizontal a 640 píxeles.

## Comprobación dirigida

Casos contrastados: Laplace de exp(−2t), su inversa causal y una Dirac; rechazo de variables incorrectas; Z de secuencias geométricas derecha e izquierda con sus condiciones; inversas derecha, izquierda y mixta; polos repetidos; impulsos en índices positivos y negativos; radio 1e-16 frente a polo 1e-15; rechazo del radio que coincide con un polo; opción sin muestras; ROC de expresiones finitas y cero/infinito.

Recorridos comprobados: entradas y resultados independientes al alternar operaciones, copia a inversa con ROC izquierda, resultado que llega mientras está activa otra operación, registro numérico opcional y presentación en anchos de 1366, 800 y 640 píxeles. La ayuda compacta y su lista bajo demanda se revisaron por separado. No se hizo una campaña general de pruebas.

## Alcance vigente

Laplace es unilateral en la directa y causal en la inversa; no ofrece selección general de ROC bilateral. Z directa trabaja con expresión y soporte o con registro finito; la inversa algebraica admite funciones racionales cuyos polos resuelve el motor. Las condiciones y los casos pendientes permanecen explícitos. Los registros gráficos son finitos y en doble precisión. Esta versión sigue siendo de desarrollo hacia 1.0; no declara que toda expresión simbólica o ejercicio de la materia sea resoluble.
