<p align="center">
  <img src="docs/assets/signallab-banner.svg" alt="SignalLab PC — laboratorio de señales y sistemas" width="1200">
</p>

<p align="center">
  <a href="https://github.com/Tincho1286/SignalLab-PC/releases/latest"><img alt="Versión estable 1.2.1" src="https://img.shields.io/badge/estable-1.2.1-71d7c4?style=flat-square&amp;labelColor=172632"></a>
  <a href="LICENSE"><img alt="Licencia GPL-3.0-or-later" src="https://img.shields.io/badge/licencia-GPL--3.0--or--later-b4a1d5?style=flat-square&amp;labelColor=172632"></a>
  <img alt="Windows y Linux portables" src="https://img.shields.io/badge/Windows%20%2B%20Linux-portables-8ab6df?style=flat-square&amp;labelColor=172632">
  <img alt="Desarrollado con Python" src="https://img.shields.io/badge/Python-3.12-b4a1d5?style=flat-square&amp;labelColor=172632">
</p>

<p align="center">
  <a href="https://github.com/Tincho1286/SignalLab-PC/releases/latest"><strong>Descargar</strong></a> ·
  <a href="docs/README.md">Documentación</a> ·
  <a href="docs/tools.md">Herramientas</a> ·
  <a href="CHANGELOG.md">Novedades</a> ·
  <a href="https://github.com/Tincho1286/SignalLab-PC/issues">Informar un problema</a>
</p>

# SignalLab PC

Un laboratorio de escritorio para **señales, sistemas y procesamiento digital**. Permite trabajar con expresiones matemáticas, muestras y funciones de transferencia, observar sus resultados y continuar el análisis en otras herramientas o en una calculadora CAS.

Está pensado para estudiar Sistemas y Señales, desarrollar cálculos y explorar cómo se relacionan el tiempo, la frecuencia y los planos de Laplace y Z. Cada herramienta tiene sus propias entradas; la biblioteca de resultados permite reutilizar lo calculado sin volver a cargar los datos.

![Modelo AR con su ecuación, transferencia y estadísticas en SignalLab PC](docs/assets/process-models.png)
<p align="center"><sub>Modelo de proceso AR: parámetros, ecuaciones y resultados en un mismo documento. Captura de la línea 1.1.</sub></p>

## Descargar y empezar

1. Elegí la descarga de tu sistema desde la versión estable:
   - **Windows:** [SignalLab-PC-1.2.1.exe](https://github.com/Tincho1286/SignalLab-PC/releases/download/v1.2.1/SignalLab-PC-1.2.1.exe).
   - **Linux x86_64:** [SignalLab-PC-1.2.1-linux-x86_64.tar.gz](https://github.com/Tincho1286/SignalLab-PC/releases/download/v1.2.1/SignalLab-PC-1.2.1-linux-x86_64.tar.gz), base Ubuntu 22.04 / glibc 2.35 o posterior.
2. En Windows abrí el `.exe`; en Linux descomprimí el archivo y ejecutá `SignalLab-PC` dentro de su carpeta. Ambos incluyen Python y las dependencias de la aplicación. [Uso y requisitos de Linux](docs/linux.md).
3. Buscá una herramienta, cargá una fórmula, muestras o un archivo y presioná **Calcular**. **F1** abre su ayuda.

Los gráficos se abren en ventanas independientes. Desde **Resultados** podés consultar, exportar y reutilizar las salidas. [Primeros pasos →](docs/getting-started.md)

> **Nuevo en 1.2.1:** aclaración visible de indeterminaciones removibles, con puntos y valores por límite en el informe, la ayuda y Resultados. [Ver novedades →](docs/releases/v1.2.1.md)

¿Windows muestra una alerta al abrir el portable? [Firma, reputación y descargas →](docs/windows-downloads.md)

## Qué podés hacer

| Área | Herramientas |
| --- | --- |
| **Señales** | Fórmulas y tramos, muestras, ventanas, edición, transformaciones, suma, producto, convolución y correlación. |
| **Sistemas LTI** | H(s)/H(z), frecuencia, fase, retardo de grupo, polos y ceros, respuesta temporal, realizaciones y espacio de estados. |
| **Diseño de filtros** | FIR e IIR por especificaciones, enventanado de h[n], diseño por raíces, modelos analógicos, ajustes y conversiones. |
| **Fourier y espectros** | DFT/FFT, DTFT, Fourier continua e inversas, series, energía espectral, periodograma, Welch, Hilbert y STFT. |
| **Muestreo y A/D** | Muestreo, aliasing, reconstrucción, conversión racional de tasa, cuantización y precisión numérica. |
| **Laplace y Z** | Directas e inversas con condiciones y ROC; ecuaciones diferenciales y en diferencias. |
| **Señales aleatorias** | Realizaciones, estadísticas, correlación, modelos AR/MA/ARMA y estimación AR por Yule–Walker. |
| **CAS** | Expresiones exactas, simplificación, ecuaciones, matrices, supuestos y operaciones sobre resultados. |

[Explorar el catálogo →](docs/tools.md) · [Convenciones matemáticas →](docs/conventions.md) · [Formatos de archivos →](docs/file-formats.md)

## Una interfaz para explorar y calcular

| Ecuaciones lineales | Diseño por polos y ceros |
| --- | --- |
| [![Ecuación en diferencias y solución algebraica](docs/assets/difference-equations.png)](docs/assets/difference-equations.png) | [![Carga binómica o polar y lista de raíces](docs/assets/pole-zero-design.png)](docs/assets/pole-zero-design.png) |

Las capturas muestran la línea 1.1. Los informes presentan fórmulas con notación matemática, los gráficos discretos usan tallos y las ayudas incluyen esquemas en colores. Las entradas modificadas conservan el resultado anterior hasta recalcularlo.

## Documentación

- [Primeros pasos](docs/getting-started.md): flujo de trabajo, atajos y resultados.
- [Herramientas](docs/tools.md): qué resuelve cada área y dónde encontrarla.
- [Alcance de Sistemas y Señales I/II](docs/scope/sys-i-ii.md) y [Señales Aleatorias](docs/scope/random-signals.md): capacidades y temas pendientes.
- [Historial de cambios](CHANGELOG.md): mejoras por versión.
- [Desarrollo](docs/development/README.md): arquitectura, dependencias, compilación y publicaciones.

Las herramientas distinguen resultados exactos, aproximaciones y cálculos pendientes. Cada método conserva sus hipótesis, unidades y condiciones de convergencia.

## Desarrollo y contribuciones

Desarrollado en **Python 3.12**, con **PySide6, NumPy, SciPy, SymPy y Matplotlib**. El código de la aplicación está en `signallab_pc/`; las descargas se distribuyen en [Releases](https://github.com/Tincho1286/SignalLab-PC/releases).

Para proponer mejoras o informar errores, consultá la [guía de contribución](CONTRIBUTING.md). Un ejemplo reproducible con la herramienta, la entrada y el resultado esperado ayuda a resolver problemas de cálculo o de interfaz.

## Licencia abierta

SignalLab PC se publica bajo **GNU GPL versión 3 o posterior**. Podés usarlo, estudiar su código, modificarlo y redistribuirlo, incluso con fines comerciales. Las versiones modificadas que se distribuyan deben conservar la licencia GPL y facilitar su código fuente conforme a sus términos. Se distribuye sin garantía.

[Licencia completa](LICENSE) · [Libre y comercial: qué significa](docs/license.md) · [Alcance y avisos](NOTICE.md) · [Licencias de terceros](THIRD_PARTY_NOTICES.md)

## Code signing policy

La 1.2.1 publicada sigue sin firma digital. Se solicitó la incorporación al servicio de SignPath Foundation el 2 de noviembre de 2026, con una compilación verificable en GitHub. La evaluación del proveedor sigue pendiente; todavía no hay un certificado concedido. [Política de firma y responsables](docs/code-signing.md) · [Privacidad](docs/privacy.md).
