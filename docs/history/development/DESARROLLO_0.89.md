# SignalLab PC 0.89 — inversas legibles y carga común de sistemas

28/10/2026. Consolidación de herramientas existentes; se mantienen las 31 familias y 72 rutas públicas.

## Inversas Z y Laplace

Los casos racionales numéricos con raíces algebraicas de grado alto muestran sus polos y coeficientes evaluados dentro de la expresión. Desaparecen de los informes las tablas de sustitución p[k]/A[k]. Los parámetros libres permanecen simbólicos: no se inventan valores para ellos.

La inversa Z conserva la descomposición exacta, la clasificación por ROC y las muestras de precisión ampliada. Se reutiliza la identificación de raíces numéricas con sus intervalos algebraicos exactos. Para la inversa Laplace causal se incorpora una vía de fracciones parciales numéricas cuando existen factores irreducibles de grado mayor que dos y no hay parámetros libres. Los casos elementales y expresiones no racionales conservan la vía simbólica existente.

Se respetan órdenes repetidos, impulsos y sus derivadas, soportes derechos/izquierdos y el valor de Heaviside en el origen. Los pares conjugados comprobados de entradas reales se agrupan como senos y cosenos. La salida numérica se identifica como aproximada. No se añade una selección de ROC bilateral a Laplace.

El texto completo conserva al menos 17 cifras significativas. La vista usa 6 para leer con comodidad, preservando cifras adicionales cerca de límites críticos como el círculo unidad. Este redondeo sólo afecta imágenes matemáticas: no modifica datos, muestras ni texto copiado/guardado. Los productos pueden continuar en otra línea con su signo de multiplicación; no se reduce la letra. El visor evita transformar estos decimales en enormes fracciones exactas. Las ayudas explican la diferencia entre cálculo y presentación.

## Cargar y reutilizar sistemas

Cargar sistema reúne dos alternativas en una sola acción: un resultado anterior y un archivo JSON de transferencia exportado por SignalLab. Se integra en análisis, respuesta temporal, precisión, herramientas de fase/ganancia, estados, diseño por polos y ceros y los dos bloques de conexiones. No se agregan rutas al explorador.

El lector común valida formato, versiones 1/2, dominio, números finitos, coeficientes, secciones SOS y avance entero. Un archivo con SOS y coeficientes contradictorios se rechaza; las dos representaciones no pueden describir sistemas distintos. Los consumidores causales rechazan avances antes de cambiar los campos o publicar un resultado. Cargar prepara datos y conserva su procedencia; el cálculo del destino sigue siendo explícito.

Se corrige la recepción en el diseñador: aceptar la transferencia ya no borra las raíces cargadas en el plano. La conversión a estados ya rechazaba avances mediante su backend de realización; se mantiene esa restricción y se incorpora el acceso común por archivo.

## Conexiones

Cada bloque admite fórmula racional o coeficientes, además de archivo/resultado. Se corrige la pérdida de avances: antes una cascada z·1 podía devolver 1; ahora devuelve z. El álgebra en cascada, paralelo y realimentación conserva potencias positivas y negativas. La cascada mantiene SOS y cancela sólo factores de desplazamiento exactamente comunes, sin modificar los sistemas recibidos.

El informe muestra la relación calculada y la transferencia completa. Analizar, reutilizar y exportar trabajan con el resultado calculado; editar un borrador lo marca como desactualizado sin reemplazarlo. No se deduce estabilidad interna ni causalidad de una mera equivalencia racional; un denominador de lazo idénticamente nulo se rechaza.

## Comprobaciones dirigidas

- Ocho métodos en test_system_flow y test_inverse_numeric_display: JSON válido/malformado, SOS/avance, las cuatro conexiones frente a evaluación directa, cancelación exacta de desplazamientos, tres ROC Z, polos repetidos, Laplace frente a respuesta de estados independiente, impulsos y casos elementales.
- Recorrido Qt: archivo en análisis/conexiones/diseño/precisión/temporal/estados, selección de H₂ desde resultado anterior, fórmula por bloque, rechazo sin mutación, resultado conservado al editar, raíces recibidas y salida numérica sin alias ni tablas.
- Revisión de carga a 1366, 800 y 640 px. Ajuste final de fórmulas en esos anchos sin desplazamiento horizontal del informe; inspección de capturas Z/Laplace y conexiones.

La revisión general del portable queda pendiente, según lo acordado. Esta entrega continúa el acercamiento a 1.0 y no declara cerrado su alcance.
