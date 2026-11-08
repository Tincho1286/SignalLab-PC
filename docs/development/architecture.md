# Arquitectura

[← Desarrollo](README.md)

SignalLab PC separa la definición de entrada, el modelo matemático, el cálculo y su presentación. Esa separación permite que un resultado conserve sus datos y condiciones aunque cambie de vista o se reutilice en otra herramienta.

| Capa | Componentes principales | Responsabilidad |
| --- | --- | --- |
| Escritorio y navegación | `workbench.py`, `toolbox.py`, `workflow_catalog.py`, `tool_catalog.py` | Documentos, herramientas, variantes y acciones de cálculo. |
| Entradas | `expression_editor.py`, `numeric_input.py`, `coefficient_editor.py`, `data_import.py`, `system_import.py` | Fórmulas, tramos, coeficientes, archivos y validación. |
| Modelos | `model.py`, `filters.py`, `state_space.py` | Señales, transferencias y estados con metadatos explícitos. |
| Cálculo | `operations.py`, `fourier.py`, `course_tools.py` y módulos especializados | Algoritmos numéricos, transformadas, filtros y procesos. |
| Álgebra | Analizadores de expresiones, `symbolic_process.py`, `cas_engine.py` | Gramática restringida, valores exactos y trabajo simbólico aislado. |
| Resultados | `project.py`, `result_journal.py`, `result_expressions.py` | Registros, procedencia y reutilización compatible. |
| Presentación | `report_view.py`, `signal_plot.py`, `plot_view.py` y ayudas | Fórmulas, tablas, figuras externas y explicaciones. |
| Actualizaciones | `update_manifest.py`, `update_download.py`, `installations.py`, `update_ui.py` | Verificación del canal, descarga e inicio del instalador. |

## Definiciones y condiciones

Las señales conservan muestras complejas, origen, paso, dominio, unidades y metadatos. Las transferencias mantienen su convención de coeficientes, secciones, avances, reloj y ROC disponibles. Los registros de Resultados añaden procedencia para que un destino pueda interpretar el objeto recibido.

Las condiciones no se deducen de una figura: una fórmula racional puede necesitar una ROC para determinar su soporte y estabilidad. Las definiciones generales que no son racionales se conservan como expresiones y no se convierten artificialmente en coeficientes finitos.

## Cálculo y representación

Los analizadores utilizan gramáticas restringidas; la capa de datos no ejecuta código Python o MATLAB arbitrario. Las operaciones largas se separan del hilo de interfaz mediante los mecanismos de trabajo y cancelación disponibles. Las expresiones exactas se mantienen antes de proyectarlas a valores numéricos cuando el método lo permite.

El dato calculado es independiente de su dibujo. Reducir puntos para representar o paginar una tabla no trunca el registro exportado. Editar una entrada marca el resultado previo como desactualizado hasta volver a calcular. Los límites de una vista complementaria se distinguen de la disponibilidad del resultado principal.

## Distribución y mantenimiento

PyInstaller construye el paquete nativo de cada sistema. Los instaladores por usuario envuelven esos paquetes y conservan una identidad estable de instalación; el actualizador comprueba el manifiesto firmado y la integridad antes de iniciarlos. La clave privada no forma parte de la aplicación ni del repositorio.

La [guía de fiabilidad](../mathematical-reliability.md) describe los controles de cálculo y de reutilización. La [guía de publicación](releases.md) explica cómo vincular binarios, fuentes y procedencia. Las decisiones de migración anteriores se conservan en el [archivo histórico](../history/README.md).
