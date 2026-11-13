# Documentación de SignalLab PC

Estas guías explican cómo instalar SignalLab PC, elegir una herramienta e interpretar sus resultados. La versión estable actual es la [1.8.3](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.8.3), disponible como instalable y portable para Windows x64 y Linux x86_64.

También está disponible la [1.8.7 preliminar](releases/v1.8.7.md), con un inspector de curvas, extremos, cursores precisos y correcciones de navegación de figuras e informes. La [guía de gráficos](cursors.md) explica esas operaciones. Conserva la [estimación AR](ar-estimation.md) de la 1.8.6 y las ampliaciones anteriores de [medidas espectrales](spectral-measurements.md), [ventanas temporales](time-frequency.md) y biblioteca por temas.

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
| Configurar colores y foto de fondo | [Temas de apariencia](appearance.md) |

## Interpretar la matemática

Las [convenciones](conventions.md) describen índices, frecuencias, normalizaciones y regiones de convergencia. La [guía de fiabilidad](mathematical-reliability.md) desarrolla el tratamiento de condiciones, singularidades removibles y resultados pendientes. Para un caso especialmente sensible al soporte elegido, consultá [Transformada Z y sinc](z-transforms.md).

La cobertura académica se detalla por separado para [Sistemas y Señales I/II](scope/sys-i-ii.md) y [Señales Aleatorias](scope/random-signals.md). Estas matrices permiten identificar tanto las herramientas disponibles como los temas y métodos todavía pendientes.

## Ayuda dentro de la aplicación

**F1** o **Ayuda** abre la página de la herramienta activa. Allí se explica qué significa cada entrada, qué condiciones requiere el método y cómo interpretar la salida. Los esquemas de bandas, ventanas, raíces y ejes relacionan los parámetros con la figura correspondiente.

## Novedades, objetivos y contribuciones

El [historial](../CHANGELOG.md) resume la evolución del software y las [notas de versiones](releases/README.md) describen cada publicación. Los [objetivos](roadmap.md) reúnen trabajo pendiente, mientras que el [archivo histórico](history/README.md) conserva documentos de etapas anteriores identificados como tales.

Para trabajar con el código, seguí la [guía de desarrollo](development/README.md). La [guía de contribución](../CONTRIBUTING.md), la [licencia](license.md) y la [política de privacidad](privacy.md) completan las condiciones de participación y uso.
