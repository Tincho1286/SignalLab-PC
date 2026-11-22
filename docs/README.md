# Documentación de SignalLab PC

Estas guías explican cómo instalar SignalLab PC, elegir una herramienta e interpretar sus resultados. La 1.9.2 ofrece instalador y portable para Windows x64 y Linux x86_64. [Descargas](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.9.2).

Esta versión muestra las actualizaciones disponibles al iniciar y detecta períodos al trabajar con señales o series de Fourier. [Notas de la 1.9.2](releases/v1.9.2.md).

La **1.9.3 preliminar** incorpora el guardado y la recuperación de sesiones. También corrige medidas de amplitud muy pequeña y la reutilización de relojes de muestreo. [Descarga de la preliminar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.9.3) · [Notas de la 1.9.3](releases/v1.9.3.md).

## Instalar y empezar

La [guía de instalación](installation.md) ayuda a elegir el paquete adecuado. Después, [Primeros pasos](getting-started.md) recorre un cálculo completo y muestra cómo continuar con su resultado. Si ya tenés la edición instalada, la [guía de actualizaciones](installed-updates.md) explica cómo incorporar nuevas versiones conservando la configuración.

| Necesitás… | Guía |
| --- | --- |
| Instalar, abrir o desinstalar | [Instalación](installation.md) |
| Actualizar desde la aplicación | [Actualizaciones](installed-updates.md) |
| Comprobar compatibilidad Linux | [Linux](linux.md) |
| Entender una alerta de Windows | [Firma y alertas](windows-downloads.md) |
| Resolver el primer problema | [Primeros pasos](getting-started.md) |

## Trabajar con datos y resultados

El [catálogo de herramientas](tools.md) organiza las operaciones por el problema que resuelven. Cada herramienta mantiene sus entradas y ofrece las acciones adecuadas para su resultado; la [guía de formatos](file-formats.md) explica cómo importar, guardar y reutilizar esos objetos sin perder su significado.

| Necesitás… | Guía |
| --- | --- |
| Encontrar una operación y conocer sus salidas | [Herramientas](tools.md) |
| Importar archivos o conservar resultados | [Formatos de datos](file-formats.md) |
| Leer figuras y utilizar cursores | [Gráficos y mediciones](cursors.md) |
| Comparar respuestas y medir el transitorio | [Respuesta temporal](temporal-responses.md) |
| Leer niveles y comprobar bandas de un filtro | [Medidas de frecuencia](frequency-measurements.md) |
| Estudiar coordenadas, equilibrios y memoria | [Estudios de estados](state-studies.md) |
| Cargar tablas, deshacer ediciones y combinar muestras | [Herramientas básicas](basic-usability.md) |
| Repetir un período y escribir trenes de pulsos o impulsos | [Señales periódicas y trenes](periodic-signals.md) |
| Medir energía temporal, componentes y cruces | [Medidas de registros](record-measurements.md) |
| Comparar reconstrucciones y explicar sus núcleos | [Reconstrucción de señales](reconstruction-studies.md) |
| Configurar colores y foto de fondo | [Temas de apariencia](appearance.md) |

## Interpretar la matemática

Las [convenciones](conventions.md) describen índices, frecuencias, normalizaciones y regiones de convergencia. La [guía de fiabilidad](mathematical-reliability.md) desarrolla el tratamiento de condiciones, singularidades removibles y resultados pendientes. Para un caso especialmente sensible al soporte elegido, consultá [Transformada Z y sinc](z-transforms.md).

La cobertura académica se detalla por separado para [Sistemas y Señales I/II](scope/sys-i-ii.md) y [Señales Aleatorias](scope/random-signals.md). Estas matrices permiten identificar tanto las herramientas disponibles como los temas y métodos todavía pendientes.

## Ayuda dentro de la aplicación

**F1** o **Ayuda** abre la página de la herramienta activa. Allí se explica qué significa cada entrada, qué condiciones requiere el método y cómo interpretar la salida. Los esquemas de bandas, ventanas, raíces y ejes relacionan los parámetros con la figura correspondiente.

## Novedades, objetivos y contribuciones

El [historial](../CHANGELOG.md) resume la evolución del software y las [notas de versiones](releases/README.md) describen cada publicación. Los [objetivos](roadmap.md) reúnen trabajo pendiente, mientras que el [archivo histórico](history/README.md) conserva documentos de etapas anteriores identificados como tales.

Para trabajar con el código, seguí la [guía de desarrollo](development/README.md). La [guía de contribución](../CONTRIBUTING.md), la [licencia](license.md) y la [política de privacidad](privacy.md) completan las condiciones de participación y uso.
