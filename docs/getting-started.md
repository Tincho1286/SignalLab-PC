# Primeros pasos

[← Documentación](README.md)

## Abrir el laboratorio

Descargá el archivo `.exe` de la [última versión estable](https://github.com/Tincho1286/SignalLab-PC/releases/latest), guardalo en una carpeta y ejecutalo. No hace falta instalar Python. Los archivos de datos y resultados se guardan en la ubicación que elijas al exportarlos.

## Resolver un problema

1. Elegí el área desde el explorador o buscá una operación con **Ctrl+K**.
2. Completá las entradas de esa herramienta. Las señales pueden definirse por fórmula, tramos, muestras, archivo o resultado compatible, según la operación.
3. Presioná **Calcular** o **Ctrl+Enter**.
4. Consultá el informe, la tabla y las figuras. Los gráficos se abren en ventanas independientes para aprovechar la pantalla.
5. Exportá la salida o elegí **Usar en otra herramienta** para continuar el análisis.

Cada herramienta conserva sus parámetros. No hace falta crear una señal global para comenzar. Si una operación usa dos señales, cada entrada tiene su fórmula, archivo, origen y resultado de referencia.

## Un primer ejemplo: una ventana

En **Señales → Crear una señal**, elegí **Ventana**, seleccioná Hann y fijá **L=17**. Al centrarla, los índices son −8,…,8. Calculá para obtener el gráfico de tallos, sus valores y el informe. Desde el resultado podés estudiar su Fourier o su Z.

L indica el número total de muestras. Cambiar el origen desplaza la señal y cambia su fase; no modifica los valores generados.

## Resultados y edición

La biblioteca **Resultados** guarda las salidas calculadas: señales, sistemas, expresiones y otros datos compatibles. Editar una entrada marca la salida anterior como desactualizada; no cambia sus datos hasta recalcular. La exportación y la reutilización toman ese último resultado calculado.

La calculadora **CAS** permite continuar operaciones simbólicas. Las expresiones conservan sus variables y condiciones; un registro numérico se representa como datos, sin inventar una fórmula infinita.

## Atajos

| Acción | Atajo |
| --- | --- |
| Buscar herramientas | Ctrl+K |
| Calcular en la herramienta activa | Ctrl+Enter |
| Abrir ayuda contextual | F1 |
| Evaluar en CAS | Enter |
| Nueva línea en CAS | Shift+Enter |

## Elegir una versión

Usá la estable para el trabajo habitual. Las preliminares permiten explorar funciones nuevas; sus notas detallan el alcance disponible. Para describir un problema, indicá la versión que aparece en el título o en **Ayuda → Acerca de SignalLab**.
