# Leer y medir los gráficos

**Abrir gráfico** aparece junto a las pestañas del resultado y del informe, con fondo y borde visibles. Al tener varias figuras, la flecha ocupa una zona propia a la derecha: pulsá el texto para abrir la figura actual o la flecha para elegir otra. Con una sola figura se muestra un botón sin menú.

En las ventanas de gráficos 2D, activá **Cursores** en la barra. La lectura aparece debajo de la figura, sin tapar los datos.

La preliminar **1.8.7** separa la navegación de los controles científicos. Zoom, desplazamiento y guardado permanecen en la barra de iconos. Las escalas, componentes y herramientas de medida se acomodan en filas visibles según el ancho disponible; no quedan ocultos los selectores dentro del menú de una barra estrecha.

1. Mové el mouse sobre una traza: A sigue el punto más cercano en su eje horizontal. En n se eligen muestras enteras. Los planos de polos y ceros utilizan coordenadas libres del mouse; las otras nubes de puntos seleccionan el punto más cercano en pantalla.
2. Hacé clic para fijar A. Al mover el mouse, B sigue la nueva posición.
3. Otro clic fija B. La tabla muestra x e y de cada cursor y las diferencias **B−A**.
4. **Seguir** o **Esc** libera ambos. Un clic después de fijar los dos empieza otro intervalo. También podés usar los botones Fijar A/B.
5. **Copiar** lleva la tabla al portapapeles con la precisión almacenada; la vista usa diez cifras significativas y las descripciones de las celdas muestran hasta diecisiete.

Los paneles con un eje compartido o explícitamente compatible se consultan juntos. En módulo, fase y retardo se ve el valor de cada traza. No se enlazan índices n con frecuencias ω ni rad/s con rad/muestra.

Desde la preliminar 1.8.7, podés **arrastrar un cursor fijo A/B** para moverlo conservando el otro. En una secuencia sigue eligiendo muestras enteras. Con el foco en la figura, las flechas izquierda/derecha recorren puntos de la traza activa. El editor de polos y ceros conserva sus gestos de diseño; los botones o la carga de coordenadas permiten medir sin editar raíces.

## Curvas, fórmulas y posición exacta

**Curvas y medidas…** abre un inspector junto a la figura. Elegí la traza y consultá **Definición**. Cuando existe una expresión guardada, se muestra con su intervalo y sus condiciones. En sistemas se distingue H(s) o H(z), su evaluación en frecuencia y la representación dibujada: módulo, dB, real, imaginaria, fase o retardo.

Las fórmulas temporales almacenadas sólo se utilizan si todavía corresponden a las muestras y al eje. Modificar valores o coordenadas invalida una definición anterior que no fue reemplazada explícitamente. Las ventanas nuevas conservan su fórmula con esa comprobación. En señales muestreadas se distingue la función continua del mapeo de índices a tiempo. Una curva de datos sin expresión algebraica lo informa; el inspector no inventa una fórmula por interpolación.

En **Coordenada x para leer** se admiten expresiones como `pi/2` o `1e-3`; los índices requieren un entero. **Ir** lee el punto disponible más cercano. Las flechas recorren el anterior o siguiente. **Lectura libre** libera los cursores; **Mover A** o **Mover B** conserva el otro. B requiere colocar A primero. Si el punto queda fuera de la vista, el eje se desplaza conservando el alcance cuando la escala lo permite.

## Máximos y mínimos

En **Extremos**, elegí entre el tramo x visible y todos los puntos disponibles. **Buscar extremos** muestra el máximo y mínimo finitos; **También extremos locales** agrega los máximos y mínimos interiores. Las mesetas quedan identificadas. No se unen tramos separados por valores no definidos ni se confunden saltos de fase principal con continuidad.

La búsqueda utiliza los datos completos asociados a la traza cuando están disponibles. Si la figura sólo conserva su selección dibujada, se indica ese alcance. Las coordenadas y valores corresponden a puntos evaluados: no certifican extremos de una función entre muestras ni permiten interpretar un polo como una altura finita.

Elegí una fila para leerla o colocar A/B allí. **Exportar extremos** guarda el CSV con las unidades de los ejes, el intervalo y el alcance utilizados. Cambiar de curva o de resultado descarta la tabla anterior. Cambiar el zoom no vuelve a buscar automáticamente: pulsá Buscar extremos para evaluar otro tramo visible. Los planos de raíces, mapas y superficies no se tratan como curvas de una variable para esta búsqueda.

## Qué se está midiendo

- Se leen puntos de los datos, sin interpolar ni suponer una fórmula entre ellos. En una superposición con rejillas distintas, cada fila indica su propia frecuencia: no se presenta una igualdad de coordenadas que no exista.
- Las vistas principales de señales mantienen acceso a sus muestras originales aunque reduzcan puntos al dibujar. Una marca puede mostrar una muestra original que no pertenecía a la selección reducida.
- Fase y retardo no definidos se indican como tales. Δy usa la representación dibujada: una fase principal puede saltar 2π; esa diferencia no es una derivada ni un retardo de grupo.
- Desde la 1.8.2, los mapas rectangulares 2D permiten fijar celdas A/B. La tabla usa filas para x, y y el valor, con columnas A, B y B−A. Se leen los datos originales y el centro de la celda seleccionada, respetando ejes invertidos y celdas de distinto tamaño. Los datos enmascarados se indican como no definidos. No se adivinan valores de imágenes RGB ni de mallas curvas; las vistas 3D mantienen su navegación habitual. Los mapas se consultan sólo sobre su propio eje vertical.
- Mientras están activos desplazamiento o zoom, se conserva esa herramienta. Los clics de edición de polos y ceros siguen destinados al diseño; allí pueden fijarse lecturas con los botones. Al agregar raíces, una cruz representa un polo y un círculo representa un cero, con su centro sobre el punto de inserción.

Los cursores no modifican los datos ni se incluyen en las imágenes exportadas. La carga de una posición fuera de la vista puede desplazar el eje horizontal. Cambiar el resultado libera las lecturas anteriores para evitar medir trazas que ya no existen.

## Comparar resultados

Abrí **Resultados → Comparar resultados** o el botón de la biblioteca. Elegí dos señales con igual dominio y unidades o dos sistemas del mismo dominio. Las opciones de B se filtran por compatibilidad.

Las señales conservan su origen y fase. Las métricas usan sólo coordenadas almacenadas exactamente coincidentes, sin relleno ni interpolación. No tener puntos comunes significa que no hay comparación numérica, no que sean iguales. El RMS es un promedio sobre los puntos comparados.

En la ventana gráfica, **Vista** permite elegir **Superponer A y B** o **Diferencia B−A**; **Componentes** cambia entre parte real/imaginaria y módulo/fase sin repetir el cálculo. **Exportar comparación CSV…**, junto a los resultados, guarda las coordenadas comunes y las componentes de A, B y B−A. No se exporta una diferencia si no hay puntos comunes. El CSV identifica las entradas no definidas y las diferencias fuera de rango.

Si existen impulsos de Dirac, el selector **Parte** de la figura distingue muestras ordinarias y pesos. El CSV exporta ambas partes con una columna que las identifica. Los pesos se comparan en la unión de sus posiciones; la ausencia de un término implica peso cero en esa posición, sin rellenar huecos de muestras ordinarias.

Las métricas distinguen una diferencia nula de un valor positivo que queda fuera del rango de float64. Los datos se capturan al calcular: editar después las fuentes no modifica el informe ni su exportación. La biblioteca registra el informe y sus dos entradas; la comparación no vuelve a publicar esas señales como resultados nuevos.

Para dos H(s) o dos H(z), elegí el intervalo angular común. Ambas se evalúan en las mismas frecuencias y el informe conserva las condiciones de cada sistema. La interpretación como Fourier requiere una ROC compatible. La comparación se registra con sus dos orígenes en la biblioteca de Resultados.

Los colores de ventanas, informes y figuras pueden elegirse desde **Vista → Tema**. La [guía de apariencia](appearance.md) describe los temas disponibles.

## Editar polos y ceros y cambiar el alcance

La ventana del plano de diseño incluye el selector **Agregar polo × / Agregar cero ○ / Mover punto / Quitar punto**. Está sincronizado con el documento de diseño. Al elegir una acción de edición se desactiva la herramienta de desplazamiento o zoom de la barra, para que el siguiente clic edite el punto elegido.

La **rueda** cambia el zoom alrededor del mouse en el plano binómico. **Acercar +** y **Alejar −** cambian la escala visible; **Ajustar a raíces** encuadra el diseño completo. En polar se modifica el alcance radial. La nueva vista se conserva al colocar raíces y actualizar el sistema. Para insertar una raíz en 2, alejá primero el plano hasta que esa posición quede visible. La carga exacta desde la lista sigue disponible y encuadra las raíces introducidas.


## Zoom del espectro de ventanas

En **Generar ventanas → Espectro de la ventana**, el dibujo se adapta al intervalo visible. Al ampliar se recuperan las muestras originales de esa región; en una vista amplia se conservan extremos locales. Los cursores consultan el espectro completo y mantienen las posiciones fijadas durante el zoom. La selección dibujada no modifica las medidas ni las muestras exportables. La escala lineal/dB se elige dentro de la figura.
