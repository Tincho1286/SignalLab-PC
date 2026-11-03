# SignalLab 0.57 · Importación MATLAB y ajustes de escritorio

## Uso

Archivo → Importar señal MATLAB permite agregar una señal al espacio de trabajo. En cada entrada local también se admite.mat o.m desde Abrir datos. Elegí variable, canal de matriz e interpretación del eje. Para tiempo continuo usá un vector de segundos o ingresá inicio y paso; para secuencias, índices enteros de paso 1. Se conservan los valores complejos y no se remuestrean ejes irregulares.

MAT: datos numéricos de formatos clásicos y 7.3/HDF5. Se inspeccionan nombres y tamaños; sólo se cargan las variables seleccionadas. No se convierten objetos, tablas ni celdas MATLAB. Las estructuras de formatos clásicos no se expanden.

M: lector de definiciones numéricas, sin ejecución del script. Admite asignaciones, constantes, vectores, matrices, rangos, linspace, zeros, ones, funciones matemáticas y operaciones escalares o elemento a elemento. No es un intérprete MATLAB completo: bucles, funciones propias, indexación, gráficos y productos/potencias matriciales requieren exportar los datos como.mat. El diálogo incluye la lista de funciones y los límites. Se rechazan instrucciones no admitidas con un mensaje; no se omiten cálculos silenciosamente.

## Escritorio y optimización

- Se usa el logo existente en la ventana y en QApplication; se fija la identidad de aplicación de Windows para la barra de tareas. El EXE también conserva su icono incorporado.
- Importación MAT selectiva, sin cargar todo el espacio MATLAB.
- La búsqueda de herramientas reutiliza textos normalizados en lugar de reprocesarlos en cada tecla.
- Dependencia HDF5 incluida tanto en instalación como en empaquetado.

## Revisión acotada

Importación clásica/HDF5, valores complejos, fórmulas.m, ejes y canales; rechazo de llamadas no admitidas; diálogo de selección; icono cargado; apertura de generación, respuesta temporal/frecuencial, FIR, muestreo y densidad de energía; publicación/reutilización y sintaxis de los módulos. No certifica todos los recorridos ni sustituye una evaluación general de uso.

## Alcance actualizado

Modulación y demodulación quedan fuera; no se agregó código de esas herramientas. Señales Aleatorias sigue postergada. La prioridad pasa a importación, funcionamiento y optimización de las herramientas existentes. Los inventarios anteriores de cobertura son históricos y no prueban por sí solos qué falta para el alcance acordado. No se declara todavía cobertura completa ni versión 1.0.
