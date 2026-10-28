# SignalLab PC 0.13.2 — edición y lectura matemática

## Cambios
- La tabla de tramos y la vista matemática utilizan una sola definición. Cambiar de vista conserva las modificaciones y no recupera una fórmula antigua.
- Al convertir una fórmula a tramos se conserva inicialmente su valor a ambos lados del origen. El usuario edita luego las condiciones y los valores.
- Reemplazar los tramos por otra fórmula es una acción explícita. El campo de fórmula no muestra la representación interna de los tramos.
- Las definiciones condicionales existentes también se abren como tramos. La primera rama incondicional conserva su prioridad; las ramas posteriores no la reemplazan.
- El editor visual también está disponible para las expresiones de Fourier y convolución/correlación algebraica.
- Los informes muestran ecuaciones con fracciones, potencias y condiciones. Se reducen los paréntesis redundantes sin suprimir agrupaciones necesarias.
- Los rótulos repetidos, por ejemplo varias condiciones de un resultado, conservan todas sus filas.

## Comprobaciones
Pasaron las 129 pruebas existentes en 28.581 segundos. También se comprobaron alternancia de vistas, equivalencia de las muestras antes y después de convertir una fórmula a tramos, lectura de condicionales, prioridad de la primera rama incondicional, ausencia de valor por defecto, nueve ejemplos de notación y conservación de rótulos repetidos.

El renderizado visual está documentado en interfaz-0.13.2-formulas.png (demostración del editor y del informe). Estas comprobaciones no acreditan la migración completa ni equivalencia general con MATLAB u Octave. Los formatos matemáticos no soportados conservan su texto original.
