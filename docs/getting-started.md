# Primeros pasos

[← Documentación](README.md)

## Abrir el laboratorio

Descargá la [versión estable](https://github.com/Tincho1286/SignalLab-PC/releases/latest) en formato instalable o portable. Ambos incluyen Python; la [guía de instalación](installation.md) explica qué archivo elegir y cómo abrirlo en Windows o Linux. Una vez en la aplicación, podés trabajar directamente en cualquier herramienta.

## Resolver un problema

Las preliminares con el nuevo escritorio reúnen la navegación en **Herramientas**. En la edición estable 1.8.14, elegí la operación desde el explorador. En ambas podés buscar con **Ctrl+K**.

1. Elegí la herramienta y completá sus entradas. Según la operación, podés usar fórmulas, tramos, muestras, archivos o resultados compatibles.
2. Presioná **Calcular** o **Ctrl+Enter**.
3. Consultá el informe o la tabla. **Abrir gráfico** abre la figura en otra ventana.
4. Exportá la salida o elegí **Usar señal en…** o **Usar filtro en…** para continuar con ese resultado.

Cada variante conserva sus parámetros. Podés volver a su área desde el enlace sobre el título. Cuando hay poco ancho, **Datos de entrada** y **Resultado** se muestran en pestañas. **Ctrl+Mayús+R** amplía el informe.

## Ejemplo: generar y estudiar una ventana

En **Señales → Crear una señal**, elegí **Ventana**, seleccioná Hann y fijá una longitud **L=17**. Al centrarla alrededor de cero, los índices van de −8 a 8. Calculá para obtener las 17 muestras, el informe y el gráfico discreto de tallos.

Desde las acciones del resultado podés enviar la ventana a Fourier o a Transformada Z, o exportarla en JSON/CSV. L es la cantidad total de muestras; para un FIR de esa longitud, el orden nominal es M=L−1. Cambiar el origen desplaza la secuencia y modifica su fase, aunque conserve los valores de la ventana.

## Continuar con un resultado

La biblioteca **Resultados** conserva las salidas calculadas y su procedencia. Una señal, una transferencia y una expresión simbólica tienen distintos destinos posibles; el menú de reutilización ofrece los compatibles con el objeto elegido. La [guía de formatos](file-formats.md) explica qué información acompaña a cada uno.

Al editar una entrada, el resultado anterior queda marcado como desactualizado hasta volver a calcular. Su registro original permanece disponible; la exportación toma el resultado calculado, no una interpretación anticipada de los campos que estés editando.

Para continuar el álgebra, enviá la expresión al **CAS**. Allí podés simplificarla, sustituir valores o resolver ecuaciones conservando las condiciones registradas. Una tabla de muestras se utiliza como datos; no se convierte por sí sola en una fórmula para todos los índices.

## Ayuda y apariencia

Presioná **F1** para consultar los parámetros, el método de cálculo y sus límites. En la Biblioteca también están **Interfaz de trabajo**, **Gráficos y cursores** y **Valores por continuidad**. En **Vista → Tema** podés elegir una paleta clara u oscura o cargar una foto. La elección se conserva al reiniciar. [Guía de apariencia](appearance.md).

## Atajos

| Acción | Atajo |
| --- | --- |
| Buscar herramientas | Ctrl+K |
| Calcular en la herramienta activa | Ctrl+Enter |
| Abrir ayuda contextual | F1 |
| Evaluar en CAS | Enter |
| Nueva línea en CAS | Shift+Enter |

## Guardar el trabajo y actualizar

Exportá los resultados o informes que quieras conservar antes de cerrar o actualizar. La configuración persiste, pero la sesión completa de resultados no se recupera automáticamente al reiniciar. La edición instalada incorpora **Ayuda → Buscar actualizaciones**; las [notas de versiones](releases/README.md) explican qué cambia en cada entrega.
