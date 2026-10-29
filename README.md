# SignalLab PC 1.1.0

Laboratorio portable para Windows de Sistemas y Señales I y II, desarrollado en Python. Versión estable 1.1: primera ampliación de Señales Aleatorias.

## Descargar y empezar

[Descargar SignalLab PC 1.1.0](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.1.0). El repositorio es privado: necesitás una cuenta con acceso para ver sus versiones y archivos.

Abrí SignalLab-PC-1.1.0.exe. Incluye Python y las dependencias; no necesitás instalarlos para usar el portable. La copia local está en outputs/SignalLab-PC-1.1.0.exe.

Elegí el problema desde Inicio, el explorador o Buscar (Ctrl+K). Cada herramienta tiene sus entradas y resultados propios. Podés cargar fórmulas o tramos, pegar muestras, importar un archivo o reutilizar un resultado compatible. Calcular (Ctrl+Enter) produce un resultado; editar los datos después no cambia silenciosamente esa salida.

Los gráficos se abren en ventanas independientes. F1 o Ayuda abre la página de la herramienta, con sus entradas, convenciones e ilustraciones. Ayuda → Acerca de SignalLab muestra la versión. Resultados permite exportar, reutilizar y enviar datos matemáticos al CAS.

## Herramientas

La navegación reúne 30 problemas y 82 variantes, más la hoja CAS.

| Área | Qué reúne |
|---|---|
| Señales | Crear, editar, transformar, sumar, multiplicar, convolucionar, correlacionar y medir energía/potencia/RMS. |
| Sistemas LTI | Análisis de H, frecuencia, respuesta temporal, polos/ceros, realizaciones, conexiones y espacio de estados. |
| Diseño de filtros | Un solo diseño para FIR/IIR por especificaciones, ventanas y h[n], raíces, segundo orden y RC; ajustes, filtros ideales y conversión. |
| Fourier y espectros | DFT/FFT, DTFT, Fourier continua, directas e inversas, series, energía espectral, PSD, Hilbert y STFT. |
| Muestreo y A/D | Muestreo, aliasing, reconstrucción, cambio de tasa, cuantización y representación numérica. |
| Laplace y Z | Transformadas directas/inversas con condiciones y ROC, y ecuaciones diferenciales. |
| Señales aleatorias | Generación y estadísticas; correlación auto/cruzada; modelos AR/MA/ARMA y estimación AR por Yule–Walker. |

La calculadora CAS trabaja con expresiones, ecuaciones, matrices, supuestos y resultados reutilizables. El software mantiene su paleta oscura, tipografía matemática vectorial y logo propio.

## Alcance de esta versión

- [Alcance y convenciones de 1.0](ALCANCE_1.0.md).
- [Notas de 1.1.0](VERSION_1.1.0.md).
- [Notas de la primera estable](VERSION_1.0.0.md).
- [Cobertura de Señales Aleatorias](COBERTURA_SENALES_ALEATORIAS.md).
- [Cobertura de Sistemas y Señales I/II](COBERTURA_SYS_I_II_ACTUAL.md).
- [Cierre y evidencia](CIERRE_1.0.md).

Las condiciones, aproximaciones numéricas y límites de cada método siguen visibles en la ayuda y los resultados. Publicar 1.0 no convierte las cuadraturas finitas en transformadas exactas ni elimina las condiciones de convergencia.

## Código, compilación y versiones

El código está en este repositorio privado. Los portables se adjuntan a Releases, fuera del historial Git. La primera versión y los ejecutables anteriores están respaldados en el archivo histórico.

Para desarrollo, setup_windows.ps1 prepara el entorno Python y build_portable.ps1 genera el ejecutable y limpia sus intermedios al terminar correctamente. [Publicar versiones](RELEASES_GITHUB.md) · [Almacenamiento](ALMACENAMIENTO.md).

Se conservan localmente la versión actual, la anterior y la primera. No se distribuyen los documentos de la materia ni credenciales. El historial previo del proyecto se conserva en las notas DESARROLLO y en docs/README_HASTA_0.99.11.md.
