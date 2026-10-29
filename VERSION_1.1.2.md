# SignalLab PC 1.1.2 · carga exacta de polos y ceros

En Diseñar filtro → Polos y ceros se incorpora un formulario a la izquierda para agregar cada raíz. Se conservan el editor con mouse, los dos dominios y las acciones de análisis y reutilización del filtro.

- Elegir Polo o Cero y la forma de carga: binómica (parte real a e imaginaria b) o polar (módulo r y ángulo θ en radianes).
- Se admiten fracciones, pi, expresiones constantes y 10^(-3). Las expresiones se conservan en las listas; la evaluación usa la precisión numérica de la aplicación.
- La opción Agregar también el conjugado se sincroniza con Pares conjugados del editor del plano. Una raíz real u origen se agrega una sola vez. Las repeticiones deliberadas conservan su multiplicidad.
- La lista se muestra por filas, con el tipo y el valor de cada raíz. Doble clic permite corregir un valor; la selección múltiple permite quitar sólo las filas elegidas. El tooltip muestra coordenadas, módulo y ángulo.
- Agregar, editar o quitar actualiza listas y plano. Diseñar desde polos y ceros calcula la nueva transferencia y su respuesta. Así se pueden cargar varias raíces antes de recalcular.
- El formato del formulario es independiente de los ejes del plano: se puede cargar en polar mientras se observa el plano binómico.
- Los múltiplos exactos de pi/2 en la carga polar se ubican sobre los ejes sin residuos artificiales. Los componentes imaginarios pequeños se conservan cuando son parte del dato.
- Mover o agregar otros puntos con el mouse conserva las expresiones de las raíces que no cambian.
- Ayuda específica con diagrama de colores para relacionar partes real/imaginaria con módulo/ángulo y conjugados.

Comprobaciones dirigidas de carga binómica/polar, conjugados, origen, ejes exactos, componente imaginaria pequeña, conservación de expresiones, edición y eliminación por fila, y ejecución del diseño desde la barra superior. Revisión visual del formulario compacto y la ayuda. No se ejecutó una batería general ni una nueva campaña del portable.
