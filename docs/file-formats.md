# Importar, exportar y reutilizar datos

[← Documentación](README.md)

## Fuentes de una entrada

Las entradas numéricas compatibles ofrecen **Fórmula**, **Muestras**, **Archivo** y **Resultado**. Cada operando puede usar una fuente diferente: por ejemplo, sumar una señal calculada con un CSV o multiplicar dos registros importados.

La importación está disponible desde el selector de Resultados y los editores algebraicos compatibles. El tipo de dato, el dominio, la variable y las unidades determinan qué puede cargarse.

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

## ROC de transferencias

Los formatos 1 a 3 conservan coeficientes, avances y reloj según su versión. El formato 4 añade ROC digital: `right`, `left` o `radius` con radio positivo. El formato 5 añade ROC analógica: `right`, `left` o `line` con una parte real `sigma` interior a la franja. Los bordes se determinan por los polos no cancelados del modelo almacenado.

La ausencia de ROC se conserva explícitamente: una expresión racional no fija por sí sola causalidad ni estabilidad bilateral. El archivo de frecuencia JSON también conserva la transferencia y su interpretación matemática. Los CSV conservan su tabla de datos habitual.

## Conservar resultados entre sesiones

La biblioteca reúne los resultados durante el trabajo. Exportar una selección permite recuperar los objetos compatibles y su procedencia; no equivale a guardar automáticamente todas las pestañas y el estado completo de una sesión. Exportá los datos e informes que quieras conservar antes de cerrar o de instalar una actualización.
