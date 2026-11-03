# Arquitectura

[← Desarrollo](README.md)

SignalLab PC separa las definiciones de entrada, los modelos matemáticos, el cálculo y la presentación. Los resultados son objetos reutilizables con su dominio, ejes y metadatos.

| Capa | Componentes principales | Responsabilidad |
| --- | --- | --- |
| Escritorio y navegación | `workbench.py`, `toolbox.py`, `workflow_catalog.py`, `tool_catalog.py` | Documentos, herramientas, variantes y acciones de cálculo. |
| Entradas | `expression_editor.py`, `numeric_input.py`, `coefficient_editor.py`, `data_import.py`, `system_import.py` | Fórmulas, tramos, coeficientes, archivos y validación de compatibilidad. |
| Modelos | `model.py`, `filters.py`, `state_space.py` | Señales, transferencias y estados con metadatos explícitos. |
| Cálculo | `operations.py`, `fourier.py`, `course_tools.py`, módulos de filtros y procesos | Algoritmos numéricos y análisis de señales/sistemas. |
| Cálculo simbólico | `symbolic.py`, `symbolic_process.py`, `cas_engine.py`, módulos de transformadas | Gramática restringida, expresiones exactas y trabajo simbólico aislado. |
| Resultados | `project.py`, `result_journal.py`, `result_expressions.py` | Instantáneas, procedencia, resultados tipados y reutilización compatible. |
| Presentación | `report_view.py`, `signal_plot.py`, `plot_view.py`, ayudas | Fórmulas vectoriales, tablas, figuras externas y explicaciones. |

## Contratos que se conservan

`Signal` mantiene muestras complejas, origen, paso, dominio, unidades y metadatos. `Transfer` conserva la convención polinómica, las secciones, el avance y el reloj disponibles; la línea 1.2 añade la ROC registrada. Los registros de Resultados conservan su procedencia.

La capa numérica no ejecuta texto Python ni archivos MATLAB arbitrarios. Las expresiones se analizan con gramáticas restringidas. Las operaciones largas usan los mecanismos de trabajo y cancelación de la aplicación.

Los controles de vista no cambian el dato calculado. Reducir puntos al dibujar o paginar una tabla no trunca el registro exportado. Cambiar entradas marca un resultado anterior como desactualizado hasta recalcularlo.

## Extensiones compartidas de 1.2

`singularities.py` comparte el tratamiento de límites removibles; `transfer_plane.py` separa la evaluación racional y la ROC de `z_plane.py`; `amplitude_design.py` define amplitudes y límites por banda; los importadores comunes sirven a selectores y entradas independientes.

Los documentos de migración anteriores se conservan en [el archivo histórico](../history/README.md), separados de esta descripción vigente.
