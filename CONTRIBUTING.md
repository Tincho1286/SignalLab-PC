# Contribuir a SignalLab PC

Las mejoras pueden proponerse mediante [Issues](https://github.com/Tincho1286/SignalLab-PC/issues) o un pull request. Antes de abrir una propuesta, revisá las [herramientas disponibles](docs/tools.md) y el [alcance](docs/scope/sys-i-ii.md).

## Informar un problema

Indicá la versión, la herramienta y los datos mínimos para reproducirlo. Para un cálculo, incluí la expresión o coeficientes, origen, unidades, método y resultado esperado. Para una interfaz, indicá resolución y escala de pantalla, y adjuntá una captura si ayuda a entender el problema.

Especificá las convenciones que utiliza el caso. La ROC, la normalización de Fourier y el origen de las muestras cambian la interpretación del cálculo y son necesarios para comparar el resultado obtenido con el esperado.

## Proponer una mejora

Explicá qué problema de señales o sistemas permitiría resolver y cómo encaja en las herramientas existentes. Un ejemplo pequeño y su resultado matemático ayudan a definir el alcance.

## Trabajar con el código

1. Prepará el entorno según la [guía de desarrollo](docs/development/README.md).
2. Hacé los cambios en una rama con un objetivo concreto.
3. Conservá los modelos de datos y las convenciones matemáticas compartidas.
4. Actualizá las ayudas y la documentación si cambia la entrada o la interpretación de una salida.
5. Describí en el pull request el comportamiento resultante, las comprobaciones realizadas y los límites pendientes.

Las correcciones de cálculo deben conservar condiciones, unidades, índices y casos no definidos. Las variantes nuevas deben reutilizar componentes comunes cuando resuelven el mismo problema.

## Documentación y versiones

La portada presenta el software, sus herramientas, las descargas disponibles y los objetivos generales. Cada párrafo desarrolla una idea central; sus oraciones deben explicar o completar esa idea. Los cambios de tema se separan en párrafos o apartados propios.

Las mejoras pendientes se describen como objetivos en `docs/roadmap.md`. Las notas de versiones registran funciones publicadas, correcciones y compatibilidad. Una preliminar que ya puede descargarse pertenece a la sección de descargas, no a un anuncio de una versión futura.

El estado de trámites, certificados y servicios de firma se documenta en las páginas técnicas correspondientes. No se añade al final del README ni se mezcla con la presentación del producto.

Los portables se adjuntan a Releases, fuera del historial Git. El historial técnico anterior se conserva en `docs/history/`.

## Licencia de las contribuciones

Las contribuciones originales al proyecto se incorporan bajo GPL-3.0-or-later. Conservá los avisos existentes y acreditá cualquier material de terceros con su licencia compatible y procedencia. Proponé únicamente contenido que tengas derecho a aportar bajo esos términos.
