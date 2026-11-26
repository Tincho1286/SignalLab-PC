<p align="center">
  <img src="docs/assets/signallab-banner.svg" alt="SignalLab PC · Laboratorio de señales y sistemas" width="1200">
</p>

<p align="center">
  <a href="https://github.com/Tincho1286/SignalLab-PC/releases/latest"><strong>Descargar Stable/LTS</strong></a> ·
  <a href="https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.1.0"><strong>Descargar Preview 2.1.0</strong></a> ·
  <a href="#engineering-core-en-develop">Engineering Core</a> ·
  <a href="docs/getting-started.md">Primeros pasos</a> ·
  <a href="docs/tools.md">Herramientas</a> ·
  <a href="docs/README.md">Documentación</a> ·
  <a href="docs/releases/README.md">Historial</a>
</p>

SignalLab PC es un laboratorio de escritorio para **Sistemas y Señales I/II y procesamiento digital de señales**. Podés calcular una transformada, diseñar un filtro o estudiar un sistema LTI con cálculo simbólico, simulación numérica e informes. Podés reutilizar los resultados en otras herramientas compatibles. La aplicación está disponible en español para Windows y Linux.

## Engineering Core en develop

La rama `develop` incorpora **Fase 02C**, dedicada a verificar la integridad científica, la compatibilidad de sesiones y los límites de ejecución. La DFT usa la misma frontera desde el escritorio, Python y la consola. Python y la consola también dan acceso a IDFT, diseño y aplicación FIR, conversión racional de tasa y densidad espectral de potencia (PSD), sin cargar Qt.

El flujo **cambio de tasa → FIR → DFT y PSD** guarda los resultados intermedios en una sesión que podés abrir en el escritorio. El Core verifica la procedencia, conserva unidades y reloj y publica el flujo completo en una transacción. Podés guardar sesiones en JSON o en `.slproj`, que almacena las muestras en binario. Ambos formatos guardan variables, historial y borrador del CAS, y la recuperación local escribe en segundo plano. La cancelación de los motores numéricos se verifica en puntos cooperativos. [Contratos de la API](docs/engineering/phase_02b/ENGINEERING_CORE_API.md) · [Auditoría y validación de Fase 02C](docs/engineering/phase_02c/README.md)

### Probar el flujo desde el código fuente

Prepará el entorno de desarrollo y ejecutá estos comandos desde la raíz del repositorio. El primero genera una señal de ejemplo y el segundo guarda el flujo en `flujo.json`. [Preparar el entorno](docs/development/README.md)

```sh
python -B tools/example_engineering_core.py work/ejemplos-core
python -m signallab_pc dsp-pipeline --signal work/ejemplos-core/entrada.json --output work/ejemplos-core/flujo.json --up 2 --down 3 --fir .25 .5 .25 --psd-method periodogram --window boxcar
```

Los ejemplos reproducibles cubren DFT, IDFT y el flujo DSP. El expediente de Fase 02C documenta la cobertura, la compatibilidad de proyectos y los instaladores comprobados en Windows y Ubuntu. [Ejemplos de Python y CLI](docs/engineering/phase_02b/ENGINEERING_CORE_EXAMPLES.md) · [Validación de 02C](docs/engineering/phase_02c/validation/FINAL_VALIDATION_MATRIX.md)

### Laboratorio de comunicaciones digitales en develop

La Fase 03 incorpora modulación PSK y QAM, diseño de pulsos RC/RRC, ruido AWGN calibrado, recuperación asistida o con piloto y mediciones BER, SER y EVM. El enlace integrado guarda las muestras, el reloj y la procedencia del experimento. Podés comparar constelaciones, señales I/Q, diagramas de ojo y espectros, o ejecutar un barrido y retomarlo desde la última corrida verificada. [Expediente y ejemplos](docs/engineering/phase_03/README.md)

La **2.1.0 Preview** está disponible como instalador y portable para Windows x64 y Linux x86_64. La entrega corresponde al SHA validado en las dos plataformas. [Descargas y novedades](docs/releases/v2.1.0.md) · [Quality Gate](docs/engineering/phase_03/QUALITY_GATE_REPORT.md)

```bash
python -m signallab_pc communications link --bits 4096 --seed 2026 --eb-n0 6 --output enlace.slproj
```

## Descargar la versión estable

**2.0.0** es la base de la familia **Stable/LTS 2.0.x**. Las entregas Preview de Engineering siguen un canal independiente que se activa explícitamente en el actualizador. [Notas de la versión](docs/releases/v2.0.0.md) · [Código fuente y sumas SHA‑256](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.0.0) · [Política de ramas y publicaciones](docs/engineering/RELEASE_POLICY.md)

| Plataforma | Instalable | Portable |
| --- | --- | --- |
| Windows x64 | [Instalador .exe](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.0.0/SignalLab-PC-2.0.0-setup.exe) | [Ejecutable .exe](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.0.0/SignalLab-PC-2.0.0.exe) |
| Linux x86_64 | [Instalador .run](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.0.0/SignalLab-PC-2.0.0-linux-x86_64.run) | [Archivo .tar.gz](https://github.com/Tincho1286/SignalLab-PC/releases/download/v2.0.0/SignalLab-PC-2.0.0-linux-x86_64.tar.gz) |

Los cuatro paquetes incluyen Python y las dependencias. Si querés actualizar desde la aplicación, elegí el instalable y abrí **Ayuda → Buscar actualizaciones**. Para ejecutar SignalLab desde una carpeta, elegí el portable. [Requisitos e instrucciones](docs/installation.md) · [Canales de actualización](docs/installed-updates.md).

<p align="center">
  <img src="docs/assets/workbench-200.png" alt="Diseño de un filtro FIR en SignalLab PC con bandas de paso, transición y rechazo" width="1080">
  <br><sub>Diseño FIR por bandas y tolerancias.</sub>
</p>

## Herramientas

| Qué querés estudiar | Qué podés hacer |
| --- | --- |
| **Señales y operaciones** | Crear fórmulas, funciones por tramos, ventanas o registros. Calcular convolución, correlación, energía, potencia y RMS. |
| **Sistemas y filtros** | Obtener H(s) o H(z) de una fórmula, coeficientes o un diagrama de bloques. Ver respuestas, polos, ceros y retardo. Diseñar FIR e IIR, enventanar h[n] y definir filtros ideales por bandas. |
| **Transformadas y ecuaciones** | Calcular Fourier, Laplace y Z con las condiciones que correspondan. Obtener inversas y resolver ecuaciones diferenciales y en diferencias con condiciones iniciales. |
| **Muestreo y espectros** | Estudiar aliasing, reconstrucción, cambio de tasa y cuantización. Comparar DFT y DTFT, probar ventanas y analizar espectros con periodograma, Welch o STFT. |
| **CAS y señales aleatorias** | Operar con expresiones, supuestos y matrices. Generar registros aleatorios, comparar estadísticas y trabajar con modelos AR, MA y ARMA. |

Consultá el [catálogo detallado](docs/tools.md) o el alcance por materia para [Sistemas y Señales I/II](docs/scope/sys-i-ii.md) y [Señales Aleatorias](docs/scope/random-signals.md).

## Flujo de trabajo

1. Abrí una herramienta desde el catálogo o buscala con **Ctrl+K**. Cada herramienta tiene sus propias entradas. **F1** abre la ayuda del cálculo activo.
2. Presioná **Calcular** y leé el informe. Desde el mismo resultado podés abrir las figuras, consultar muestras con el cursor o comparar curvas.
3. Usá **Usar señal en…** o **Usar filtro en…** para continuar en otra herramienta. Desde **Resultados** podés exportar objetos e informes. **Archivo → Sesiones** guarda el trabajo para retomarlo después.

Por ejemplo, podés diseñar un FIR por tolerancias, revisar sus bandas y usar ese mismo filtro en una respuesta temporal. [Primeros pasos](docs/getting-started.md) · [Gráficos y mediciones](docs/cursors.md) · [Sesiones y formatos](docs/file-formats.md).

## Novedades de la 2.0.0

El nuevo escritorio agrupa las variantes en un selector que se puede abrir desde el informe o los datos. La ayuda sigue el método activo y los avisos de validación llevan al campo que hay que corregir. En diseños FIR e IIR, el esquema de bandas muestra sus bordes con acceso directo a los parámetros.

Las figuras permiten elegir una curva de referencia y seguir sus muestras con los cursores. En **Resultados** podés distinguir tipos de salida, abrir gráficos guardados y seguir los vínculos con los datos que originaron cada cálculo. [Notas completas](docs/releases/v2.0.0.md) · [Historial de cambios](CHANGELOG.md).

## Proyecto abierto

Podés revisar las [convenciones matemáticas](docs/conventions.md), consultar los [objetivos del proyecto](docs/roadmap.md) o preparar un entorno con la [guía de desarrollo](docs/development/README.md). Si encontrás un problema de cálculo o de uso, incluí los datos de entrada y el resultado esperado en [Issues](https://github.com/Tincho1286/SignalLab-PC/issues/new/choose). [Cómo contribuir](CONTRIBUTING.md).

SignalLab PC se distribuye bajo [GPL-3.0-or-later](LICENSE). [Guía de la licencia](docs/license.md) · [Avisos de terceros](THIRD_PARTY_NOTICES.md) · [Privacidad](docs/privacy.md).
