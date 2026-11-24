# Contribuir a SignalLab PC

El [catálogo de herramientas](docs/tools.md) y el [alcance académico](docs/scope/sys-i-ii.md) ayudan a ubicar cada cambio dentro del laboratorio.

## Informar un problema

Abrí un [informe de error](https://github.com/Tincho1286/SignalLab-PC/issues/new?template=bug_report.yml) con la versión de SignalLab, el sistema operativo y los pasos para reproducirlo.

- Para un cálculo, pegá la fórmula o los coeficientes y describí el resultado obtenido y el esperado. Incluí las condiciones que cambien el significado del ejercicio, como el índice inicial, las unidades, el soporte o la región de convergencia.
- Para un problema visual, indicá qué acción hiciste, la resolución y la escala de pantalla. Una captura ayuda si muestra la parte afectada.

## Proponer una mejora

Enviá una [propuesta](https://github.com/Tincho1286/SignalLab-PC/issues/new?template=feature_request.yml) con el problema que querés resolver y un ejemplo de entrada y salida. Si el flujo ya existe en otra herramienta, explicá cómo lo usás y qué paso querés mejorar.

## Preparar un cambio de código

1. Configurá el entorno con la [guía de desarrollo](docs/development/README.md) y trabajá en una rama.
2. Respetá las [convenciones matemáticas](docs/conventions.md) y conservá las condiciones junto con el resultado. Para una corrección de cálculo, incluí un caso que reproduzca el error y cubra la regla que se modificó.
3. Si cambia el uso o el significado de un resultado, actualizá la ayuda y la guía correspondiente.
4. En el pull request, describí el efecto en la aplicación y las comprobaciones que ejecutaste.

Las contribuciones originales se incorporan bajo [GPL-3.0-or-later](LICENSE). Conservá los avisos existentes y acreditá el material de terceros con su procedencia y licencia.
