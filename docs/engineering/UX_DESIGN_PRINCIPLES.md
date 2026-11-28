# Diseño del Workbench

El formulario inicial muestra lo necesario para resolver la tarea habitual. Los métodos especializados se eligen dentro del mismo flujo y conservan los datos y resultados compatibles.

## Conservar las rutas conocidas

Evolucionar el Workbench, navegación por disciplinas, catálogo, familias, `WorkflowSelector`, variantes, búsqueda global, favoritos, recientes, pestañas, paneles acoplables, espacio de trabajo y ayuda contextual. Mantener las figuras y las acciones para abrir, exportar o reutilizar resultados en sus puntos de acceso habituales. Preservar identificadores, restauración de sesiones y enlaces de ayuda.

## Mostrar opciones según el problema

- Ubicar los parámetros esenciales en el formulario inicial y justificar científicamente sus valores predeterminados.
- Usar secciones desplegables, variantes, selectores de método, controles contextuales o pestañas de salida para parámetros especializados. Conservar a la vista las hipótesis, unidades, advertencias y condiciones necesarias para interpretar un resultado.
- Mantener un flujo con niveles de detalle accesibles. Fase 05 aplicó el patrón a las distribuciones, modelos y experimentos. El selector determina qué parámetros, diagnósticos e hipótesis aparecen. Los siguientes laboratorios deben comprobar sus propios recorridos. [Auditoría de Fase 05](phase_05/AUDIT_AND_SCOPE_REPORT.md)
- Mantener coherencia entre etiqueta, valor por defecto, documentación y contrato del motor. Comprobar que el usuario pueda volver a una variante sin perder entradas ni atribuir un resultado anterior a parámetros recién editados.

## Agrupar por tarea

Más distribuciones amplían el generador existente. Otros estimadores amplían el análisis de PSD. Los algoritmos FIR amplían el diseñador y nuevas métricas se agregan a los informes. Los modelos estadísticos se ubican en su familia. Una tarjeta nueva responde a una tarea distinta y se justifica con un recorrido concreto.

Si crece la barra lateral, revisar primero desplazamiento y agrupación por disciplinas. Adoptar navegación jerárquica si facilita la búsqueda medida en escenarios de uso. Aprovechar búsqueda global, favoritos y recientes. Los cambios de organización conservan la identidad visual y funcional del Workbench.

En Fase 09 evaluar en conjunto el catálogo, los flujos entre laboratorios, la biblioteca de resultados y la comparación de estudios. La consolidación debe preservar la identidad visual, las rutas históricas, los favoritos y la restauración de documentos. [Inventario y rutas](TOOL_INVENTORY.md) · [Modernización](TOOL_MODERNIZATION_PLAN.md#fase-09--plataforma-integrada)

## Medir el rendimiento por tramo

| Medición | Protocolo para cada cambio relevante |
| --- | --- |
| Inicio de aplicación | Medir desde un proceso nuevo hasta trabajo disponible. Registrar sistema, equipo, versión, configuración y caché. |
| Primera apertura | Medir el tiempo hasta que el formulario de la herramienta esté listo, con documento ausente en esa sesión. |
| Navegación entre documentos abiertos | Preparar los recorridos, alternar con borradores, permitir el procesamiento de eventos y registrar mediana, p95 y número de alternancias. |
| Gráficos | Separar cálculo, activación del botón, dibujo inicial e interacción en figura. Medir con ejes y volumen de datos representativos del dominio. |
| Memoria | Registrar RSS antes y después de abrir herramientas, al mostrar figuras y al cerrar documentos. Indicar la carga y el máximo observado. |

Conservar la preparación por documento y el dibujo diferido acreditados en Fase 05. Una precarga debe justificar con mediciones su efecto sobre inicio, primera apertura, cambios de menú y memoria. Los 50 cambios entre documentos abiertos de la medición local de Fase 05 pasaron de 184,8 a 39,4 ms de mediana, con Qt offscreen en Windows. Es una línea base de navegación para ese recorrido. [Método y resultados](phase_05/IMPLEMENTATION_LOG.md#navegación-entre-herramientas)

## Comprobar el recorrido

Ejercitar entrada, cálculo, informe, figura, traspaso de resultados y reapertura. Incluir errores, cambios de variante, cancelación y recuperación donde correspondan. Las comprobaciones de interfaz automatizadas son parte del Quality Gate de Windows y Linux. Las pruebas de DPI, resoluciones o multimonitor sirven para reproducir defectos y explorar ergonomía. El propietario realiza la aceptación funcional sobre sus equipos. [Validación](VALIDATION_MATRIX.md#criterios-vigentes) · [Publicaciones](RELEASE_POLICY.md)
