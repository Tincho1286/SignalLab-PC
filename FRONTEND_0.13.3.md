# SignalLab PC 0.13.3 — matrices y resultados de sistemas

## Interfaz
- A, B, C y D se editan en tablas separadas, con dimensiones de filas y columnas explícitas.
- Se pueden pegar bloques rectangulares separados por tabuladores o comas. Las celdas vacías del bloque se interpretan como cero. Los bloques irregulares se rechazan antes de modificar la matriz.
- Se admite copia de selecciones rectangulares. Las celdas muestran su valor completo al pasar el cursor.
- Al reducir dimensiones se ocultan celdas; al volver a ampliar se recuperan mientras no se cargue otro modelo. Esta conducta se indica en los controles.
- Informes y gráficos de estados y análisis de sistemas tienen pestañas con todo el alto disponible. Discretización y conversión a transferencia no muestran una pestaña de gráfico vacía.
- Matrices de resultados con dimensiones y corchetes, independientes de las fuentes instaladas. Se muestran hasta 12 cifras significativas; la representación numérica del modelo no cambia. Las vistas grandes se limitan a 20 filas y 12 columnas y avisan que son parciales.
- Los literales decimales de la vista matemática conservan los dígitos escritos, evitando un redondeo previo al componer la fórmula.

## Alcance de la verificación
Se comprobaron edición compleja, reducción y ampliación de dimensiones, pegado con una celda inicial vacía, rechazo de un bloque irregular sin modificar datos, discretización desde el editor, dimensiones de resultados y conservación de literales decimales en la presentación. Las pruebas existentes del proyecto también se ejecutaron.

El archivo interfaz-0.13.3-matrices.png documenta la presentación revisada. Los cálculos de sistemas y sus convenciones no se ampliaron en esta revisión. La migración completa y la paridad con HP siguen pendientes.
