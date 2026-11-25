# Primeros pasos

[← Documentación](README.md)

## Abrir el laboratorio

Descargá la [versión estable](https://github.com/Tincho1286/SignalLab-PC/releases/latest) en formato instalable o portable. Ambos incluyen Python; la [guía de instalación](installation.md) explica qué archivo elegir y cómo abrirlo en Windows o Linux. Una vez en la aplicación, podés trabajar directamente en cualquier herramienta.

## Resolver un problema

Elegí un área en la barra lateral para explorar su catálogo. **Ctrl+K** abre **Acceso rápido** desde cualquier página. Podés buscar una variante por su nombre, por una abreviatura como **IFFT** o por lo que querés hacer. Consultas como **Z inversa** y **respuesta al escalón discreta** abren la herramienta con esas opciones ya seleccionadas. También podés cambiar a un documento abierto o encontrar un resultado guardado por su nombre.

1. Elegí la herramienta y completá sus entradas. Según la operación, podés usar fórmulas, tramos, muestras, archivos o resultados compatibles.
2. Presioná **Calcular** o **Ctrl+Enter**.
3. Consultá el informe o la tabla. **Abrir gráfico** abre la figura en otra ventana.
4. Exportá la salida o elegí **Usar señal en…** o **Usar filtro en…** para continuar con ese resultado.

Si un dato impide calcular, el aviso aparece en **Datos de entrada**. Cuando el aviso identifica un campo, **Ir al campo** te lleva directamente a él. Podés corregirlo y recalcular. El último resultado calculado sigue disponible.

**Variante**, debajo del título, muestra las opciones de la herramienta. Podés abrir el selector con **Alt+V**, incluso desde el resultado ampliado. Cada variante conserva sus parámetros y su último cálculo. Si una variante ya abierta admite los datos de la anterior, **Copiar entrada** permite transferirlos.

En ventanas angostas, **Datos de entrada** y **Resultado** se muestran en pestañas, y el selector **Vista** reúne las salidas del resultado cuando hace falta espacio. **Ctrl+Mayús+R** amplía el resultado.

Al escribir una fórmula o una lista, debajo del eje se actualizan la primera coordenada, la última y la cantidad de valores. Para una señal de **Archivo** o **Resultados**, elegí **Revisar datos** para ver su intervalo, su gráfico y sus muestras antes de calcular. **Explorar resultados** permite esa misma revisión antes de elegir la entrada.

La estrella agrega la variante abierta a **Favoritos**. Podés reabrirla desde **Inicio** o **Acceso rápido**. Para conservar sus datos de entrada entre sesiones, guardá la sesión completa.

En el **Editor de realización**, la pestaña **Ecuaciones** muestra qué señales entran a cada bloque y con qué signo. Podés conectar una misma salida a las dos entradas de un sumador. Si los signos son opuestos, esos términos se cancelan. Elegí **Usar diagrama** y después **Calcular** para obtener la transferencia.

## Ejemplo con una ventana Hann

En **Señales → Crear una señal**, elegí **Ventana**, seleccioná Hann y fijá una longitud **L=17**. Al centrarla alrededor de cero, los índices van de −8 a 8. Calculá para obtener las 17 muestras, el informe y el gráfico discreto de tallos.

Desde las acciones del resultado podés enviar la ventana a Fourier o a Transformada Z, o exportarla en JSON/CSV. L es la cantidad total de muestras; para un FIR de esa longitud, el orden nominal es M=L−1. Cambiar el origen desplaza la secuencia y modifica su fase, aunque conserve los valores de la ventana.

## Diseñar por bandas o estudiar el muestreo

En **Diseñar filtro → Bandas y tolerancias**, seleccioná el tipo de filtro. Cada número del esquema lleva al campo que controla ese borde. Los anchos de transición se actualizan al editar y las tolerancias muestran los límites de amplitud que se usarán en el diseño.

En **Nyquist y aliasing**, **Abrir gráfico** ofrece la coincidencia temporal de las muestras y la ubicación del alias en la banda principal. Al reconstruir o cambiar la tasa de un registro con reloj, los datos heredados se pueden consultar en los campos. Activá la opción de cambiar el reloj si querés ingresar otro.

## Continuar con un resultado

En **Valores**, usá **Coordenada** para ir a un índice, tiempo o frecuencia. Si el eje es continuo, la tabla selecciona el punto almacenado más cercano. **Fila** cuenta desde 1, también en secuencias que empiezan en índices negativos. Seleccioná celdas y usá **Ctrl+C** para copiar con la precisión almacenada. El menú **Copiar** también permite llevarte filas completas o la página con sus encabezados.

En **Resultados**, buscá por nombre, operación o dominio. Las filas de señales y espectros indican el intervalo del eje y la cantidad de valores. Consultá **Informe** o **Valores** en el detalle y usá **Abrir gráfico** para abrir la figura del registro guardado. **Recorrido** muestra los datos de origen y qué resultados los usaron. Podés seguir esos vínculos y volver al registro anterior conservando los filtros.

**Abrir herramienta** lleva a la operación que generó el resultado cuando quedó registrada. **Comparar** y **Sesión** están junto al buscador.

La biblioteca **Resultados** conserva las salidas calculadas y su procedencia. Una señal, una transferencia y una expresión simbólica tienen distintos destinos posibles; el menú de reutilización ofrece los compatibles con el objeto elegido. La [guía de formatos](file-formats.md) explica qué información acompaña a cada uno.

Al editar una entrada, el resultado anterior queda marcado como desactualizado hasta volver a calcular. Su registro original permanece disponible; la exportación toma el resultado calculado, no una interpretación anticipada de los campos que estés editando.

Al recibir un resultado de otra herramienta, el destino abre sus datos de entrada y muestra la procedencia. **Volver al origen** recupera la herramienta o el registro desde el que lo enviaste. **Ver en Resultados** abre el registro que se usó como entrada.

Para continuar el álgebra, enviá la expresión al **CAS**. Allí podés simplificarla, sustituir valores o resolver ecuaciones conservando las condiciones registradas. Una tabla de muestras se utiliza como datos; no se convierte por sí sola en una fórmula para todos los índices.

En el CAS, **Comandos…** busca por operación o por sintaxis. Las plantillas actúan sobre el texto seleccionado cuando corresponde. El selector **Ir a un cálculo…** lleva a una entrada previa y activa las acciones de su resultado sin modificar el borrador.

## Ayuda y apariencia

En los editores de expresiones, **Funciones** inserta una función compatible con la variable del campo y abre la referencia de sintaxis y argumentos. **Vista previa** muestra la fórmula en notación matemática. En las definiciones por tramos, **Vista matemática** muestra la expresión completa.

Presioná **F1** para abrir la guía de la herramienta activa. **Campos**, **Esquemas** y **Leer la salida** llevan a esas secciones de la guía. En el diseño por bandas y tolerancias, la ayuda muestra primero el esquema del tipo de filtro seleccionado. **Volver al cálculo** recupera la herramienta con sus datos de entrada. Si abrís la Biblioteca desde la barra lateral, podés buscar por nombre, tema o argumento y filtrar por tipo de artículo. En ventanas angostas, **Catálogo** cambia a la búsqueda y al seleccionar un artículo volvés a la lectura.

En **Vista → Tema** podés elegir una paleta clara u oscura o cargar una foto. La elección se conserva al reiniciar. [Guía de apariencia](appearance.md).

## Atajos

| Acción | Atajo |
| --- | --- |
| Buscar herramientas | Ctrl+K |
| Elegir una variante | Alt+V |
| Calcular en la herramienta activa | Ctrl+Enter |
| Abrir ayuda contextual | F1 |
| Evaluar en CAS | Enter |
| Nueva línea en CAS | Shift+Enter |

## Guardar el trabajo y actualizar

Usá **Archivo → Sesiones → Guardar sesión completa** antes de cerrar o actualizar cuando quieras conservar los resultados, las entradas compatibles y las herramientas abiertas. Para compartir una salida individual, exportala desde el resultado. [Sesiones y formatos](file-formats.md).

En la edición instalada, **Ayuda → Buscar actualizaciones** permite consultar y descargar una versión compatible. Las [notas de versiones](releases/README.md) explican qué cambia en cada entrega.
