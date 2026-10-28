> Referencia histórica: este documento conserva el estado de su fecha. Para prioridades y evidencia vigentes, consultar [CIERRE_1.0.md](CIERRE_1.0.md) y [README.md](README.md). Algunas carencias aquí mencionadas fueron cubiertas después; no es una lista actual de bloqueos.

> Orden vigente de cierre: CIERRE_1.0.md. Por indicación del usuario, guardado/recuperación quedan fuera de los requisitos actuales. Prioridad: funcionalidad y exactitud de cálculo.

> Alcance actualizado 0.57: modulación y demodulación excluidas por el usuario. Prioridad actual: importación MATLAB, optimización y revisión de las herramientas existentes. Ver DESARROLLO_0.57.md.

# Pendientes para la primera versión estable

> Actualización de prioridades 0.54: el usuario confirma el portable y asume las revisiones generales 1 y 2. Los puntos 3, 4 y 5 se tratarán gradualmente. La etapa activa es completar herramientas de Sistemas I/II; Señales Aleatorias queda para después. Ver COBERTURA_SYS_I_II_0.54.md. La lista siguiente conserva el diagnóstico histórico, no es un bloqueo de la etapa actual.

Revisión: 25/10/2026 · Base de trabajo: 0.53 preview.

La nueva interfaz está implementada y tiene revisiones puntuales. Eso no certifica todos los recorridos, tamaños de pantalla ni resultados. Una versión estable requiere cerrar los puntos siguientes; el número 0.53 no representa un 53 % de avance.

## Imprescindibles para la primera estable

1. **Completar la consistencia de los paneles.** Revisar que cada herramienta acepte datos propios, muestre el resultado correspondiente y marque cuándo quedó desactualizado. Unificar formularios que todavía conservan disposiciones anteriores. Verificar tamaños de ventana y escalas de Windows: controles alcanzables, gráficos legibles, títulos y leyendas sin superposición.
2. **Cerrar los recorridos de reutilización.** Señal o filtro → resultado → otra herramienta → nuevo cálculo → exportación. Conservar eje, unidades, dominio, período, coeficientes y representación SOS cuando corresponda. Evitar cambios silenciosos de normalización o representación.
3. **Asegurar guardado y recuperación.** Las sesiones guardan resultados y entradas registradas, pero no todos los formularios sin calcular. Resolver la recuperación de ese trabajo o advertir claramente antes de perderlo. Comprobar abrir/guardar, cambios pendientes, cancelación del guardado, archivos dañados y fallos de escritura. La distribución del escritorio se recuerda localmente desde 0.52.
4. **Validar los cálculos con referencias pequeñas y trazables.** Casos representativos por familia: energía/Parseval, convolución, DTFT/DFT, muestreo, filtros y transformadas. Documentar tolerancias y convenciones; identificar discontinuidades, singularidades, ROC, aproximaciones numéricas y filtros de orden alto. No se propone repetir baterías extensas: el usuario prioriza mejoras y pruebas de uso propias.
5. **Terminar la documentación y los mensajes.** Ayuda coherente con los campos reales y con cada motor numérico/simbólico. Explicar fronteras, unidades, datos no válidos y limitaciones sin mostrar errores internos al usuario. La referencia de funciones elementales se incorpora en 0.53; aún falta auditar el resto de las páginas.
6. **Cerrar la candidata portable.** Probar el EXE en una PC sin Python, con escalado de Windows y rutas habituales; revisar apertura, cancelación, operaciones largas y cierre sin perder trabajo. Resolver incidencias críticas y preparar notas de versión y alcance declarado.

## Cobertura académica aún incompleta

Estas carencias siguen dentro del objetivo general del proyecto. No todas representan un fallo de estabilidad de las herramientas existentes, pero hay que declarar cuáles entran en el alcance de la primera estable.

Prioridad Sistemas y Señales I/II:
- Hilbert y señal analítica.
- STFT/espectrograma.
- Convolución por bloques: overlap-add y overlap-save.
- Diseño analógico general por especificaciones y realizaciones con componentes.
- Ampliar ventanas/diseños FIR y unificar prototipos analógicos IIR.
- Aclarar y ampliar los límites de transformadas bilaterales y regiones de convergencia.

Etapa posterior de Señales Aleatorias:
- Análisis por conjuntos, estacionariedad y ergodicidad.
- Identificación AR/MA/ARMA y estimación espectral paramétrica.
- Procesos de Markov y Poisson.
- Detección MAP/Bayes/Neyman–Pearson.
- Estimación MMSE, Wiener y Kalman; calidad e incertidumbre de estimadores.

La matriz detallada está en ALCANCE_Y_ESTABILIDAD_0.50.md. Su inventario temático sigue siendo referencia; su descripción de navegación y ayuda fue reemplazada por las entregas 0.51–0.53.

## Orden de cierre

Primero paneles y recorridos de datos, luego persistencia y documentación, después los casos de referencia y el portable candidato. No se fija fecha ni porcentaje sin evidencia. Una compilación exitosa y las revisiones puntuales actuales no bastan para declarar 1.0.
