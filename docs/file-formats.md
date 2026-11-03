# Importar, exportar y reutilizar datos

[← Documentación](README.md)

## Fuentes de una entrada

Las entradas numéricas compatibles ofrecen **Fórmula**, **Muestras**, **Archivo** y **Resultado**. Cada operando puede usar una fuente diferente: por ejemplo, sumar una señal calculada con un CSV o multiplicar dos registros importados.

La preliminar 1.2 amplía la importación desde el selector de Resultados y desde editores algebraicos compatibles. El tipo de dato, el dominio, la variable y las unidades determinan qué puede cargarse.

| Formato | Datos y uso |
| --- | --- |
| JSON de señal | Muestras complejas, origen, paso, dominio, unidades, expresión y metadatos. |
| CSV/TSV | Tabla de eje y valores. Los CSV propios incluyen metadatos; en archivos externos se eligen columnas, separador y unidades. |
| MATLAB `.mat` | Variables numéricas compatibles, con selección de variable, canal y eje. |
| MATLAB `.m` | Subconjunto admitido por el importador de datos. No es un intérprete general de MATLAB. |
| JSON de sistema | Numerador, denominador, dominio, secciones cuando existen, avances, reloj y ROC registrada según versión del formato. |
| JSON de Resultados | Selección exportada con sus datos y dependencias. Permite recuperar objetos compatibles y su procedencia. |
| JSON algebraico | Expresión, variable y condiciones de un cálculo compatible. |

## Ejes y metadatos

Una secuencia discreta requiere índices enteros de paso uno. Un registro continuo o espectral necesita un eje uniforme para las operaciones que trabajan con una señal de paso constante. Las tablas no uniformes de análisis de frecuencia conservan su formato de análisis; no se convierten en señales uniformes.

Los valores complejos conservan sus partes real e imaginaria. Cuando se registran, el reloj físico y las unidades acompañan a los datos. La importación no convierte automáticamente entre tiempo continuo y discreto, ni entre rad/s y rad/muestra.

## Señales y expresiones

Una tabla finita no define por sí sola una fórmula infinita, un período o una ROC. Usá los registros en las herramientas numéricas y las expresiones en los editores algebraicos compatibles. Un impulso Dirac continuo se conserva por posición y peso, separado de las muestras ordinarias.

## Exportación

Las señales pueden exportarse a JSON y CSV. Los sistemas usan su JSON de transferencia y, cuando corresponde, tablas de respuesta en frecuencia. Los informes se pueden copiar o guardar desde su vista. **Resultados** reúne las opciones disponibles para cada objeto.
