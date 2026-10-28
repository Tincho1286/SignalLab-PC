# SignalLab PC 0.78.1 · fórmulas del resultado al ajustar fase

27/10/2026. Corrección de presentación; no se modifican los algoritmos de reflexión de ceros, factorización ni clasificación de fase.

## Resultado visible

En Ajustar ganancia y fase → Fase mínima / paso todo, el informe muestra primero la fórmula del sistema seleccionado: Hm(z), factor con ceros reflejados, o Hap(z), paso todo y retardo. Incluye sus coeficientes, el otro factor, el H(z) original y la relación H=Hm·Hap.

El selector actualiza la fórmula, la gráfica y el sistema que se exporta o reutiliza. Editar después las entradas conserva las fórmulas del último cálculo, con el aviso de datos modificados. Cambiar sólo la vista del gráfico conserva la posición de lectura del informe.

Las ecuaciones se adaptan al ancho del panel. Para expresiones largas se muestra una suma finita con los coeficientes b[k]/a[k] de cada sistema indicado; no se omite la fórmula por su orden. Copiar texto y Guardar texto incluyen el polinomio desarrollado. La vista usa hasta 12 cifras significativas; la exportación del filtro y la reutilización conservan los coeficientes almacenados.

La comprobación de fase lineal y simetría se refiere al sistema de entrada. Se conservan las condiciones existentes para afirmar fase mínima estricta, polos estables y ceros en el círculo unidad. La ayuda de la misma herramienta explica los factores y la selección.

## Comprobación dirigida

Recorrido con H(z)=(z^(-1)-2 z^(-2))/(1-0.25 z^(-1)): se verificó que las fórmulas cortas representen los valores de los factores calculados y que Hm·Hap reproduzca H en las frecuencias revisadas. Se comprobó selección de ambos factores, exportación del seleccionado, conservación del cálculo tras editar entrada, fórmulas sin desplazamiento horizontal a 800×600 y 640×480, y un FIR de 18 coeficientes con fórmula compacta definida y texto desarrollado. Se revisaron capturas del informe. No se realizó una campaña general de pruebas.

Se mantienen la calculadora CAS, la UI oscura y todas las herramientas de 0.78. El portable anterior se conserva.
