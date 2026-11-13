<p align="center">
  <img src="docs/assets/signallab-banner.svg" alt="SignalLab PC — laboratorio de señales y sistemas" width="1200">
</p>

<p align="center">
  <a href="https://github.com/Tincho1286/SignalLab-PC/releases/latest"><img alt="Versión estable 1.8.2" src="https://img.shields.io/badge/estable-1.8.2-71d7c4?style=flat-square&amp;labelColor=172632"></a>
  <a href="LICENSE"><img alt="Licencia GPL-3.0-or-later" src="https://img.shields.io/badge/licencia-GPL--3.0--or--later-b4a1d5?style=flat-square&amp;labelColor=172632"></a>
  <img alt="Instaladores y portables para Windows y Linux" src="https://img.shields.io/badge/Windows%20%2B%20Linux-instaladores%20y%20portables-8ab6df?style=flat-square&amp;labelColor=172632">
  <img alt="Python 3.12" src="https://img.shields.io/badge/Python-3.12-b4a1d5?style=flat-square&amp;labelColor=172632">
</p>

<p align="center">
  <a href="https://github.com/Tincho1286/SignalLab-PC/releases/latest"><strong>Descargar</strong></a> ·
  <a href="docs/getting-started.md">Primeros pasos</a> ·
  <a href="docs/tools.md">Herramientas</a> ·
  <a href="docs/releases/README.md">Novedades</a> ·
  <a href="https://github.com/Tincho1286/SignalLab-PC/issues">Informar un problema</a>
</p>

# SignalLab PC

SignalLab PC es un laboratorio de escritorio para estudiar **señales, sistemas y procesamiento digital**. Combina cálculo simbólico, simulación numérica y gráficos para relacionar una definición matemática con su comportamiento en el tiempo, la frecuencia y los planos de Laplace y Z. Está orientado al aprendizaje de Sistemas y Señales I/II y al análisis de problemas de laboratorio; también incorpora herramientas de señales aleatorias.

Cada herramienta tiene sus propias entradas y puede utilizarse de manera independiente. Después de calcular, la biblioteca **Resultados** permite consultar la salida, exportarla o enviarla a otra operación compatible. Este recorrido evita volver a escribir una señal, un filtro o una expresión cuando el análisis continúa en otra herramienta.

## Descargar

La versión estable **1.8.2** está disponible para Windows x64 y Linux x86_64. Los cuatro paquetes incluyen Python y las dependencias de la aplicación; no hace falta instalar Python por separado.

| Formato | Cuándo elegirlo | Windows x64 | Linux x86_64 |
| --- | --- | --- | --- |
| **Instalable** | Para tener accesos en el sistema y actualizar desde la aplicación. | [Instalador .exe](https://github.com/Tincho1286/SignalLab-PC/releases/download/v1.8.2/SignalLab-PC-1.8.2-setup.exe) | [Instalador .run](https://github.com/Tincho1286/SignalLab-PC/releases/download/v1.8.2/SignalLab-PC-1.8.2-linux-x86_64.run) |
| **Portable** | Para ejecutar la aplicación desde una carpeta, sin registrar una instalación. | [Ejecutable .exe](https://github.com/Tincho1286/SignalLab-PC/releases/download/v1.8.2/SignalLab-PC-1.8.2.exe) | [Paquete .tar.gz](https://github.com/Tincho1286/SignalLab-PC/releases/download/v1.8.2/SignalLab-PC-1.8.2-linux-x86_64.tar.gz) |

En Windows, abrí el archivo elegido. En Linux, el instalador se inicia con `sh ./SignalLab-PC-1.8.2-linux-x86_64.run`; el portable se descomprime para ejecutar `SignalLab-PC` dentro de su carpeta. La [guía de instalación](docs/installation.md) explica ambos recorridos y enlaza los requisitos y las posibles alertas del sistema.

### Actualizar una instalación

La edición instalada ofrece **Ayuda → Buscar actualizaciones**. Podés consultar las novedades, descargar la versión nueva y elegir cuándo instalar y reiniciar, sin desinstalar antes. Los temas y la configuración se conservan; los resultados de una sesión deben guardarse o exportarse antes del reinicio.

La comprobación al iniciar se puede desactivar y no descarga ni instala por sí sola. El actualizador verifica la firma del manifiesto y la integridad del instalador antes de ejecutarlo. La [guía de actualizaciones](docs/installed-updates.md) explica este proceso y la diferencia entre esa verificación y la firma que reconoce Windows.

## Herramientas disponibles

| Área | Qué permite estudiar |
| --- | --- |
| **Señales** | Definir fórmulas, tramos y muestras; generar ventanas; desplazar, invertir, sumar o multiplicar señales; calcular convolución, correlación, energía, potencia y RMS. |
| **Sistemas LTI** | Analizar H(s) y H(z), respuestas temporales y en frecuencia, fase, retardo de grupo, polos y ceros; trabajar con conexiones, realizaciones y espacio de estados. |
| **Filtros** | Diseñar FIR e IIR por bandas y tolerancias; enventanar una h[n] propia; ubicar polos y ceros; ajustar fase y convertir entre filtros analógicos y digitales. Los filtros ideales se pueden definir por tramos en frecuencia. |
| **Fourier y espectros** | Calcular DFT/FFT, DTFT, Fourier continua e inversas disponibles; estudiar series, densidades espectrales, periodograma, Welch, Hilbert y STFT. |
| **Muestreo y precisión** | Explorar muestreo, aliasing, reconstrucción, cambios de tasa, cuantización y efectos de la representación numérica en señales y filtros. |
| **Laplace, Z y ecuaciones** | Obtener transformadas e inversas con sus condiciones; resolver ecuaciones diferenciales y en diferencias lineales con coeficientes constantes y condiciones iniciales. |
| **Señales aleatorias** | Generar registros, estimar estadísticas y correlaciones, analizar modelos estacionarios AR/MA/ARMA y ajustar modelos AR mediante Yule–Walker. |
| **Calculadora CAS** | Operar con expresiones, ecuaciones, matrices y supuestos; simplificar resultados y continuar cálculos simbólicos recibidos desde otras herramientas. |

El [catálogo de herramientas](docs/tools.md) describe las entradas y salidas de cada área. Las matrices de [Sistemas y Señales I/II](docs/scope/sys-i-ii.md) y [Señales Aleatorias](docs/scope/random-signals.md) distinguen las capacidades disponibles de los temas pendientes y de las restricciones de cada método.

## Cómo se trabaja

Elegí una herramienta desde el explorador o buscala con **Ctrl+K**. Completá sus entradas y presioná **Calcular**; el resultado reúne el informe, las fórmulas y las opciones de tabla o gráfico que correspondan. **F1** abre la ayuda de la herramienta activa, con explicaciones de los parámetros y de la interpretación del cálculo.

Las figuras se abren en ventanas independientes y las secuencias discretas se representan mediante tallos. Los cursores permiten consultar muestras y comparar dos posiciones sin modificar los datos calculados. La [guía de gráficos](docs/cursors.md) explica qué se mide en cada tipo de vista y cómo ajustar el alcance del plano de polos y ceros.

Para continuar un análisis, usá **Usar señal en…**, **Usar filtro en…** o la acción de reutilización disponible junto al resultado. La aplicación conserva el tipo de objeto y las condiciones registradas, y ofrece destinos compatibles. Por ejemplo, una ventana generada en Señales puede pasar a Fourier; un filtro diseñado puede analizarse en frecuencia o utilizarse en una respuesta temporal.

La biblioteca **Resultados** conserva las salidas durante el trabajo. Para guardarlas fuera de la sesión, exportá los objetos o informes que necesites. La [guía de formatos](docs/file-formats.md) explica JSON, CSV/TSV y los formatos MATLAB admitidos, así como los datos necesarios para conservar índices, unidades y frecuencia de muestreo.

## Interpretar los cálculos

Los informes distinguen expresiones simbólicas, aproximaciones numéricas y operaciones pendientes. También conservan las condiciones que cambian el significado del resultado, como el soporte de una secuencia o su región de convergencia. Una fórmula y una tabla finita no representan necesariamente el mismo objeto; las [convenciones matemáticas](docs/conventions.md) explican esas diferencias.

El alcance depende del método elegido y de sus hipótesis. Una evaluación sobre una rejilla no certifica todos los puntos de una función, y el motor simbólico puede dejar una expresión sin resolver. La [guía de fiabilidad](docs/mathematical-reliability.md) describe los criterios y controles utilizados, sin presentar esas comprobaciones como una garantía de resolución universal.

## Novedades e historial

La [1.8.2](docs/releases/v1.8.2.md) amplía las mediciones en espectrogramas y mapas, permite ver y exportar B−A y recupera detalle en el espectro de ventanas al hacer zoom. La [guía de gráficos](docs/cursors.md) relaciona esas vistas con sus unidades, datos originales y condiciones de comparación. Está disponible en el canal estable de actualizaciones.

La [1.8.1 estable](docs/releases/v1.8.1.md) amplía las herramientas de análisis y reúne todas las mejoras posteriores a la 1.8.0. La [guía de análisis interactivo](docs/interactive-analysis.md) explica cómo comparar filtros, seleccionar condiciones y consultar los nuevos inspectores.

La [versión 1.8.0](docs/releases/v1.8.0.md) incorpora los instaladores y el canal de actualizaciones, manteniendo los portables y las mejoras matemáticas de la [1.7.0](docs/releases/v1.7.0.md). El [historial de cambios](CHANGELOG.md) ofrece un recorrido resumido; las [notas de cada versión](docs/releases/README.md) explican las incorporaciones, correcciones y límites de cada entrega.

## Vistas de la aplicación

![Análisis de un modelo AR y sus estadísticas](docs/assets/process-models.png)

El análisis de procesos relaciona la definición del modelo con su ecuación, su transferencia y las estadísticas resultantes.

| Ecuaciones en diferencias | Diseño por polos y ceros |
| --- | --- |
| [![Solución de una ecuación en diferencias](docs/assets/difference-equations.png)](docs/assets/difference-equations.png) | [![Carga binómica y polar de raíces](docs/assets/pole-zero-design.png)](docs/assets/pole-zero-design.png) |

Las capturas corresponden a la línea 1.1 y sirven como referencia de las herramientas; no representan todos los cambios visuales posteriores. La [guía de apariencia](docs/appearance.md) explica los temas actuales y la configuración de una imagen de fondo.

## Documentación y desarrollo

El [índice de documentación](docs/README.md) reúne las guías de uso, los criterios matemáticos y la cobertura académica. Para empezar, seguí [Primeros pasos](docs/getting-started.md); para explorar las mejoras pendientes, consultá los [objetivos del proyecto](docs/roadmap.md), que no asignan fechas ni versiones a funciones todavía no publicadas.

La aplicación está desarrollada en Python 3.12 con PySide6, NumPy, SciPy, SymPy y Matplotlib. La [guía de desarrollo](docs/development/README.md) describe la estructura, las dependencias y la construcción. Para informar un problema o proponer una contribución, consultá [CONTRIBUTING.md](CONTRIBUTING.md).

## Licencia

SignalLab PC se distribuye bajo **GNU GPL versión 3 o posterior**. Podés usarlo, estudiar su código, modificarlo y redistribuirlo, incluso con fines comerciales, conforme a sus términos. Las versiones modificadas que se distribuyan deben conservar la GPL y facilitar su código fuente según la licencia. El software se distribuye sin garantía y las dependencias conservan sus propios avisos.

[Licencia](LICENSE) · [Uso y redistribución](docs/license.md) · [Avisos de terceros](THIRD_PARTY_NOTICES.md) · [Privacidad](docs/privacy.md)
