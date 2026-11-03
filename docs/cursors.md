# Leer y medir los gráficos

En las ventanas de gráficos 2D, activá **Cursores** en la barra. La lectura aparece debajo de la figura, sin tapar los datos.

1. Mové el mouse sobre una traza: A sigue el punto más cercano en su eje horizontal. En n se eligen muestras enteras. Los planos de polos y ceros utilizan coordenadas libres del mouse; las otras nubes de puntos seleccionan el punto más cercano en pantalla.
2. Hacé clic para fijar A. Al mover el mouse, B sigue la nueva posición.
3. Otro clic fija B. La tabla muestra x e y de cada cursor y las diferencias **B−A**.
4. **Seguir** o **Esc** libera ambos. Un clic después de fijar los dos empieza otro intervalo. También podés usar los botones Fijar A/B.
5. **Copiar** lleva la tabla al portapapeles con la precisión almacenada; la vista usa diez cifras significativas y las descripciones de las celdas muestran hasta diecisiete.

Los paneles con un eje compartido o explícitamente compatible se consultan juntos. En módulo, fase y retardo se ve el valor de cada traza. No se enlazan índices n con frecuencias ω ni rad/s con rad/muestra.

## Qué se está midiendo

- Se leen puntos de los datos, sin interpolar ni suponer una fórmula entre ellos. En una superposición con rejillas distintas, cada fila indica su propia frecuencia: no se presenta una igualdad de coordenadas que no exista.
- Las vistas principales de señales mantienen acceso a sus muestras originales aunque reduzcan puntos al dibujar. Una marca puede mostrar una muestra original que no pertenecía a la selección reducida.
- Fase y retardo no definidos se indican como tales. Δy usa la representación dibujada: una fase principal puede saltar 2π; esa diferencia no es una derivada ni un retardo de grupo.
- Los mapas muestran las coordenadas del puntero y el valor de la celda. La medición A/B se aplica a trazas y nubes de puntos. Las vistas 3D mantienen su navegación habitual.
- Mientras están activos desplazamiento o zoom, se conserva esa herramienta. Los clics de edición de polos y ceros siguen destinados al diseño; allí pueden fijarse lecturas con los botones. Al agregar raíces, una cruz representa un polo y un círculo representa un cero, con su centro sobre el punto de inserción.

Los cursores son elementos de consulta: no cambian datos ni límites automáticos y no se incluyen en los archivos de imagen exportados. Cambiar el resultado libera las lecturas anteriores para evitar medir trazas que ya no existen.

## Comparar resultados

Abrí **Resultados → Comparar resultados** o el botón de la biblioteca. Elegí dos señales con igual dominio y unidades o dos sistemas del mismo dominio. Las opciones de B se filtran por compatibilidad.

Las señales conservan su origen y fase. Las métricas usan sólo coordenadas almacenadas exactamente coincidentes, sin relleno ni interpolación. No tener puntos comunes significa que no hay comparación numérica, no que sean iguales. El RMS es un promedio sobre los puntos comparados.

Para dos H(s) o dos H(z), elegí el intervalo angular común. Ambas se evalúan en las mismas frecuencias y el informe conserva las condiciones de cada sistema. La interpretación como Fourier requiere una ROC compatible. La comparación se registra con sus dos orígenes en la biblioteca de Resultados.

Los colores de ventanas, informes y figuras pueden elegirse desde **Vista → Tema**. La [guía de apariencia](appearance.md) describe los temas disponibles.
