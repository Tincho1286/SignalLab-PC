# SignalLab PC 0.86 — ejecución con precisión finita

27/10/2026. Avance hacia 1.0 dentro de Cuantización y representación → Formatos y ejecución. Se conservan las 31 familias y 72 rutas; no se añade otro menú por caso.

## Qué incorpora

El estudio Filtrar con precisión finita calcula una entrada local mediante H(z), cargado por fórmula, coeficientes o resultado. Acepta señales reales/complejas, muestras, archivos y datos anteriores. La salida es una secuencia independiente, exportable y reutilizable en Fourier, análisis temporal y otras herramientas compatibles.

La realización es II transpuesta; las SOS recibidas se mantienen en su orden y escala cuando se elige conservarlas. Los coeficientes se cuantizan una vez, con a[0]=1 implícito. El orden de recurrencia sigue las ecuaciones publicadas en las [notas de lfilter de SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.lfilter.html#notes); los redondeos se insertan explícitamente en cada etapa y no se supone una multiplicación/suma fusionada.

- Formatos Q y binary16/32/64. Aritmética exacta racional entre conversiones, evitando redondear antes en doble precisión.
- Redondear productos, sumas, salida y memorias, o sólo salida y memorias. En complejos se ejecutan los cuatro productos y las dos sumas reales; también se cuantizan por componentes.
- Bits enteros extra para el acumulador Q. Conversión Q por redondeo con empates alejando de cero o truncamiento hacia cero. Saturación o complemento a dos cíclico durante la ejecución; el almacenamiento de coeficientes Q usa saturación en ambos modos.
- Memoria inicial como un valor para todos los retardos o una lista completa. En SOS, dos memorias por sección, en el orden recibido. No se confunden con salidas anteriores.
- Ceros añadidos para observar cola y ciclos. La repetición exacta del vector de estado con entrada nula confirma periodicidad de esta realización; se distingue del reposo. El detector usa memoria proporcional al estado y no guarda el historial completo. No observar un ciclo en el registro no prueba su inexistencia.

## Comparación y resultados

El informe separa dos referencias en doble precisión: filtro/entrada/memoria originales, y los mismos datos ya cuantizados sin redondeos posteriores. La segunda comparación aísla el error de ejecución. Incluye máximos y RMS escalados, SNR del registro y contadores de cambios y desbordes por etapa. La escala evita desbordar al comparar valores grandes; no es un error relativo punto a punto.

Las figuras externas comparten índices y usan muestras sin unir: parte real, imaginaria y error de ejecución. Salida y ofrece la secuencia, tabla, CSV/JSON y envío a otras herramientas. La comparación tiene CSV con entrada, salida y ambas referencias. Si una referencia desborda en doble precisión, se marca N/D y las métricas informan cuántos puntos finitos se usaron; una salida finita calculada no se descarta por ese motivo.

El JSON de salida conserva formatos, redondeo, coeficientes codificados, sistema de origen, estados iniciales/finales exactos, contadores y ciclo detectado. Las acciones de filtro reutilizan Hq, que representa coeficientes almacenados: no transportan el redondeo interno. El sistema con precisión finita puede dejar de ser lineal.

## Interfaz y ayuda

El estudio aparece en la herramienta existente. Los campos específicos se muestran según formato y estudio. Los formularios apilan etiquetas/campos y usan desplazamiento vertical. La ayuda de la misma página incluye una ilustración de colores para productos, acumulador y memorias, además de la palabra IEEE existente; también se actualizan campos, catálogo y búsqueda.

## Límites explícitos

El modelo flotante estudia valores redondeados, incluidos subnormales. No reproduce flags de procesador, modos de excepción ni el signo de cero. Un desborde flotante detiene el cálculo sin reemplazar el resultado válido anterior. Las salidas/tablas/figuras usan doble precisión; valores exactos de Q fuera de su rango se rechazan con explicación, evitando mostrar un cero o infinito falso.

El análisis de error/SNR se refiere al registro, sin suponer ruido blanco independiente. No es una teoría estadística general del ruido ni cubre todas las formas de implementación. Sigue pendiente la reconstrucción general módulo/fase y los alcances documentados en CIERRE_1.0.md; no se declara cerrada 1.0.

## Evidencia dirigida

Cuatro pruebas pasaron: casos manuales Q con productos y acumulador ampliado; saturación frente a desborde cíclico y ciclo de entrada cero frente a reposo; redondeo IEEE16 frente a operaciones escalares independientes y SOS complejas frente a SciPy; referencia no finita con salida finita, JSON estricto y errores de formato/memoria. El grupo tardó 0.23 s localmente.

Recorrido Qt dirigido: cálculo de ciclo, referencias/ejes/cursor enteros, salida independiente, CSV y JSON, entrada enviada desde otra herramienta, Hq enviado a respuesta temporal, resultado conservado al editar borrador, biblioteca y modo numérico previo. Ventanas de 640/800 sin desplazamiento horizontal del formulario. Se inspeccionaron capturas del informe, figura y ayuda; se corrigió el pie de una caja ilustrada que se cortaba. Sin campaña general de pruebas del portable.
