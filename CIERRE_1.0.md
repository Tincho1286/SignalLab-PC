# Cierre de SignalLab 1.0

Base: 1.0.0 · 29/10/2026. La primera estable consolida el alcance implementado y documentado; las revisiones futuras son mantenimiento y ampliación.

| Requisito de entrega | Evidencia de la base |
|---|---|
| Encontrar herramientas sin un menú por caso | tool_catalog.py, workflow_catalog.py y workflow_choices.py: 29 problemas, 80 rutas únicas y siete áreas; selección y búsqueda precisas, diseño agrupado y análisis separado. |
| Datos independientes y reutilización opcional | LocalInput, LocalContext y workflow_inputs.py; ResultJournal/project registran resultados; expresiones, sistemas, muestras y CAS mantienen sus rutas de reutilización. Recorridos documentados de 0.99.5–0.99.11. |
| Resultados y estado coherentes | ResultState distingue entradas efectivas de campos derivados; RC/FIR, selector oculto y edición durante cálculo comprobados en el cierre. Se conserva el último resultado y su procedencia. |
| Gráficos y fórmulas legibles | plot_view.py, signal_plot.py, plot_scale.py y math_display.py; figuras externas, tallos/índices y ejes compatibles, SVG para fórmulas. Evidencia visual y dirigida acumulada en notas DESARROLLO. |
| Ayuda accesible | Las 80 rutas tienen ayuda; biblioteca con conceptos, funciones, referencia de campos y diagramas. F1 sigue la herramienta activa. |
| Herramientas de Sistemas I/II | Matriz vigente y alcances particulares documentados. No se atribuye cobertura universal de todos los ejercicios, teoremas o modelos. |
| Portable e identidad | Proceso de compilación existente confirmado por el usuario; nombre estable, versión en título/Acerca de, logo y dependencias incluidas. |
| GitHub y almacenamiento | Código privado versionado, portables en Releases, hashes de adjuntos y retención actual/anterior/primero. |

La evidencia dirigida del cierre está en VERSION_1.0.0.md. El alcance publicado es ALCANCE_1.0.md. La revisión general de uso y portable fue asumida por el usuario; no se sustituye por baterías extensas.

Los límites matemáticos declarados se mantienen como límites del método, no como promesas de capacidades ausentes. Las incidencias concretas posteriores se atienden con versiones de mantenimiento.

El registro completo hasta 0.99.11 se conserva en docs/CIERRE_HASTA_0.99.11.md y el historial de código de GitHub. Los planes anteriores son referencias históricas, no listas vigentes de bloqueos.
