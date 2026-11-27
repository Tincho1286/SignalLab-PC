# Diseño del Workbench

El formulario inicial muestra lo necesario para resolver la tarea habitual. Los métodos especializados se eligen dentro del mismo flujo y conservan los datos y resultados compatibles.

## Conservar las rutas conocidas

Evolucionar el Workbench, navegación por disciplinas, catálogo, familias, `WorkflowSelector`, variantes, búsqueda global, favoritos, recientes, pestañas, paneles acoplables, espacio de trabajo y ayuda contextual. Mantener las figuras y las acciones para abrir, exportar o reutilizar resultados en sus puntos de acceso habituales. Preservar identificadores, restauración de sesiones y enlaces de ayuda.

## Mostrar opciones según el problema

- Ubicar los parámetros esenciales en el formulario inicial y justificar científicamente sus valores predeterminados.
- Usar secciones desplegables, variantes, selectores de método, controles contextuales o pestañas de salida para parámetros especializados. Conservar a la vista las hipótesis, unidades, advertencias y condiciones necesarias para interpretar un resultado.
- Mantener un único flujo con distintos niveles de detalle accesibles para todos los usuarios. La Fase 05 será el piloto. Empezará por seleccionar una distribución o modelo, ingresar sus parámetros esenciales y decidir qué resultados mostrar. Las opciones de ajuste, diagnóstico e incertidumbre aparecerán al aplicar el método correspondiente.
- Mantener coherencia entre etiqueta, valor por defecto, documentación y contrato del motor. Comprobar que el usuario pueda volver a una variante sin perder entradas ni atribuir un resultado anterior a parámetros recién editados.

## Agrupar por tarea

Más distribuciones amplían el generador existente. Otros estimadores amplían el análisis de PSD. Los algoritmos FIR amplían el diseñador y nuevas métricas se agregan a los informes. Los modelos estadísticos se ubican en su familia. Una tarjeta nueva responde a una tarea distinta y se justifica con un recorrido concreto.

Si crece la barra lateral, revisar primero desplazamiento y agrupación por disciplinas. Adoptar navegación jerárquica si facilita la búsqueda medida en escenarios de uso. Aprovechar búsqueda global, favoritos y recientes. Los cambios de organización conservan la identidad visual y funcional del Workbench.

## Comprobar el recorrido

Ejercitar entrada, cálculo, informe, figura, traspaso de resultados y reapertura. Incluir errores, cambios de variante, cancelación y recuperación donde correspondan. Las comprobaciones de interfaz automatizadas son parte del Quality Gate de Windows y Linux. Las pruebas de DPI, resoluciones o multimonitor sirven para reproducir defectos y explorar ergonomía. El propietario realiza la aceptación funcional sobre sus equipos. [Validación](VALIDATION_MATRIX.md#criterios-vigentes) · [Publicaciones](RELEASE_POLICY.md)
