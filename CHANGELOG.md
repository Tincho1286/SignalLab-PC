# Historial de cambios

La versión estable actual es la [1.8.3](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.8.3). Este recorrido resume la finalidad de cada entrega; las notas enlazadas desarrollan sus cambios, compatibilidad y límites. Los objetivos pendientes se consultan en la [hoja de ruta](docs/roadmap.md).

## 1.8.7 · Preliminar

La lectura de figuras incorpora un inspector con definiciones almacenadas, búsqueda de extremos y colocación precisa de cursores. A/B se pueden arrastrar conservando el otro punto y las herramientas científicas se acomodan en filas visibles. Se corrige la reapertura de la respuesta en frecuencia tras vistas alternativas y el ciclo de reajuste que hacía saltar informes. Las fórmulas se conservan con sus condiciones y se invalidan cuando cambian sus datos. Incluye toda la tanda AR de la 1.8.6; la 1.8.3 continúa estable.

[Novedades completas](docs/releases/v1.8.7.md)

## 1.8.6 · Preliminar

Estimar AR incorpora mínimos cuadrados condicionales y orden cero, comparación de órdenes sobre respuestas comunes, validación con un tramo reservado, pronóstico con intervalos y diagnóstico residual con Ljung–Box. Conserva Yule–Walker y la generación con semilla; los modelos, tablas y curvas se registran y reutilizan con sus condiciones. La ayuda distingue entrenamiento, reserva y futuro mediante un esquema en colores. La 1.8.3 continúa estable.

[Novedades completas](docs/releases/v1.8.6.md)

## 1.8.5 · Preliminar

Medir un espectro reúne varias bandas, fracción acumulada, centro, ancho RMS y detección de picos. Distingue energía, potencia y área de respuesta, conserva las coordenadas medidas y permite seleccionar bandas desde la figura sin recalcular silenciosamente. La STFT genera curvas reutilizables de potencia por banda con reloj y unidades. La ayuda explica esas medidas con un esquema en colores y mantiene la biblioteca organizada de la 1.8.4. La 1.8.3 sigue siendo estable.

[Novedades completas](docs/releases/v1.8.5.md)

## 1.8.4 · Preliminar

Esta entrega conserva los artículos y accesos de la biblioteca en 11 temas con títulos breves. Amplía STFT con escalas cuantitativas, inspección de ventanas, reconstrucción con control de cobertura y ejes y exportaciones que respetan el reloj y la fase. El inspector OLA/OLS permite estudiar historia, contribuciones y descartes conservando la convolución completa. Incluye instaladores actualizables y portables para Windows y Linux; la 1.8.3 continúa siendo estable.

[Novedades completas](docs/releases/v1.8.4.md)

## 1.8.3 · Estable

Esta entrega mejora el acceso a gráficos con un botón visible y un selector separado, permite convertir tasas por frecuencia de salida y consultar el FIR antialias real, y agrega operaciones rápidas del CAS con precisión configurable y conservación del borrador. El actualizador permite elegir estables o incluir preliminares firmadas compatibles. Incluye instaladores y portables para Windows y Linux y conserva las herramientas de la 1.8.2.

[Novedades completas](docs/releases/v1.8.3.md)

## 1.8.2 · Estable

Esta entrega incorpora lecturas A/B de celdas en mapas, una vista de diferencias y exportación CSV en la comparación de resultados, y detalle adaptativo al ampliar el espectro de ventanas. También conserva diferencias pequeñas junto a valores enormes y separa los pesos de Dirac de las muestras ordinarias. Incluye instaladores y portables para Windows y Linux, con el manifiesto firmado del canal estable.

[Novedades completas](docs/releases/v1.8.2.md)

## 1.8.1 · Estable

Esta entrega incorpora comparaciones FIR con igual longitud o tolerancias, selección visual de ROC en Z y Laplace, inspectores de ecuaciones en diferencias y convolución discreta, y medidas espectrales de ventanas. Reúne todas las mejoras posteriores a la 1.8.0 en paquetes independientes para Windows y Linux.

[Novedades completas](docs/releases/v1.8.1.md)

## 1.8.0 · Estable

La versión 1.8.0 incorpora ediciones instalables y actualizables para Windows x64 y Linux x86_64. Los portables continúan disponibles y utilizan los mismos motores de cálculo; la entrega conserva las herramientas y mejoras de estabilidad de la 1.7.0.

[Novedades completas](docs/releases/v1.8.0.md)

## 1.7.0 · Estable

La versión 1.7.0 reúne mejoras de estabilidad y fiabilidad matemática en transformadas, sistemas, filtros y CAS. El trabajo se concentra en conservar la definición y las condiciones del resultado, distinguir los problemas numéricos de los simbólicos y facilitar la continuación del análisis entre herramientas.

[Novedades completas](docs/releases/v1.7.0.md)

## 1.6.17 · Estable

Esta versión estable reúne las correcciones de las preliminares 1.6.16 y 1.6.17. Amplía el reconocimiento de pares y propiedades fundamentales, corrige casos degenerados válidos y elimina restricciones que impedían resolver tareas elementales.

[Novedades completas](docs/releases/v1.6.17.md)

## 1.6.16-preview · Preliminar

Esta entrega mejora la separación entre el resultado matemático y sus vistas complementarias. Las fórmulas, los sistemas y los modelos calculados se conservan cuando no puede generarse un gráfico, una realización numérica o una vista con formato. El informe indica qué etapa quedó pendiente.

[Novedades completas](docs/releases/v1.6.16-preview.md)

## 1.6.15 · Estable

Esta versión estable integra las correcciones publicadas en las preliminares 1.6.12 a 1.6.15. Reúne las acciones de reutilización junto al resultado y mejora la relación entre la expresión obtenida, sus muestras y las condiciones necesarias para continuar el cálculo.

[Novedades completas](docs/releases/v1.6.15.md)

## 1.6.14-preview · Preliminar

Esta preliminar mejora el intercambio entre filtros, transformadas y CAS, con especial atención a la periodicidad de Fourier, las condiciones de frecuencia y el reloj de los sistemas digitales.

[Novedades completas](docs/releases/v1.6.14-preview.md)

## 1.6.13-preview · Preliminar

Esta preliminar corrige la interpretación de objetos reutilizados y varias operaciones numéricas. Su objetivo es que un resultado mantenga el mismo significado al pasar de una herramienta a otra.

[Novedades completas](docs/releases/v1.6.13-preview.md)

## 1.6.12-preview · Preliminar

Esta preliminar mejora la reutilización de expresiones y la presentación de respuestas temporales. Las acciones de envío y los datos transferidos se organizan alrededor del resultado calculado.

[Novedades completas](docs/releases/v1.6.12-preview.md)

## 1.6.11 · Estable · Hotfix

Este hotfix incorpora expresiones de las respuestas temporales y mejora la reutilización de filtros definidos en frecuencia. Incluye la actualización posterior del intercambio con CAS distribuida dentro de esta misma versión.

[Novedades completas](docs/releases/v1.6.11.md)

## 1.6.10 · Estable · Hotfix

Este hotfix estable corrige la conservación del dominio en el CAS, la lectura de datos importados y la continuidad de los cálculos entre herramientas.

[Novedades completas](docs/releases/v1.6.10.md)

## 1.6.9 · Estable

Esta versión estable integra las mejoras de las preliminares 1.6.6, 1.6.7 y 1.6.8. Refuerza el tratamiento del dominio en el CAS y protege el cálculo de STFT frente a amplitudes extremas.

[Novedades completas](docs/releases/v1.6.9.md)

## 1.6.8-preview · Preliminar

Esta preliminar corrige transformadas numéricas y medidas espectrales, manteniendo el significado de las muestras y de los ejes al reutilizar resultados.

[Novedades completas](docs/releases/v1.6.8-preview.md)

## 1.6.7-preview · Preliminar

Esta preliminar mejora la reutilización de registros finitos y la coherencia entre índices, reconstrucción temporal y métodos espectrales.

[Novedades completas](docs/releases/v1.6.7-preview.md)

## 1.6.6-preview · Preliminar

Esta preliminar corrige el transporte de señales y espectros, la región de convergencia de sistemas conectados y varios problemas de precisión numérica.

[Novedades completas](docs/releases/v1.6.6-preview.md)

## 1.6.5 · Estable

La versión 1.6.5 hace automática la búsqueda de longitud FIR por bandas y tolerancias, incluida Kaiser. También incorpora las correcciones de Fourier distribuidas dentro de esta misma entrega.

[Novedades completas](docs/releases/v1.6.5.md)

## 1.6.3-preview · Preliminar

Esta preliminar agiliza el diseño FIR por bandas y mejora la lectura de sus gráficos. También corrige condiciones y metadatos al trasladar modelos entre herramientas.

[Novedades completas](docs/releases/v1.6.3-preview.md)

## 1.6.2-preview · Preliminar

Esta preliminar corrige la conservación de regiones de convergencia y la evaluación de fase en sistemas y transformadas.

[Novedades completas](docs/releases/v1.6.2-preview.md)

## 1.6.1-preview · Preliminar

Esta preliminar reúne correcciones de respuesta temporal, soporte activo de secuencias y reapertura de gráficos.

[Novedades completas](docs/releases/v1.6.1-preview.md)

## 1.6.0 · Estable

La versión estable 1.6.0 integra las mejoras matemáticas de la serie 1.5 y unifica la ubicación de las acciones para abrir figuras.

[Novedades completas](docs/releases/v1.6.0.md)

## 1.5.10-preview · Preliminar

Esta entrega preliminar mejora la evaluación numérica de sistemas y la interpretación del soporte de las secuencias.

[Novedades completas](docs/releases/v1.5.10-preview.md)

## 1.5.9-preview · Preliminar

Esta preliminar reúne correcciones de funciones elementales, valores en bordes e intercambio de sistemas con CAS.

[Novedades completas](docs/releases/v1.5.9-preview.md)

## 1.5.8-preview · Preliminar

Esta preliminar reúne correcciones de interpretación de impulsos y pares de transformadas.

[Novedades completas](docs/releases/v1.5.8-preview.md)

## 1.5.7-preview · Preliminar

Esta entrega reúne correcciones de cálculo, intercambio de resultados e importación.

[Novedades completas](docs/releases/v1.5.7-preview.md)

## 1.5.6-preview · Preliminar

Esta preliminar corrige el análisis de filtros ideales con escalones y hace visibles los fallos de acciones y presentación que podían parecer botones sin respuesta.

[Novedades completas](docs/releases/v1.5.6-preview.md)

## 1.5.5-preview · Preliminar

Esta entrega corrige el análisis de filtros ideales obtenidos desde Transformada Z y la apertura de gráficos de Fourier algebraica.

[Novedades completas](docs/releases/v1.5.5-preview.md)

## 1.5.4-preview · Preliminar

Esta entrega corrige la reutilización de transferencias no racionales entre Transformada Z y Análisis de sistemas.

[Novedades completas](docs/releases/v1.5.4-preview.md)

## 1.5.3-preview · Preliminar

Esta entrega incorpora un control preventivo de variaciones matemáticas y corrige inconsistencias detectadas al revisar convergencia y formas equivalentes de sistemas.

[Novedades completas](docs/releases/v1.5.3-preview.md)

## 1.5.2-preview · Preliminar

Esta entrega corrige el reconocimiento algebraico de pares Z desplazados y amplía las propiedades del par sinc/rectángulo.

[Novedades completas](docs/releases/v1.5.2-preview.md)

## 1.5.1-preview · Preliminar

Esta entrega amplía la revisión matemática a las principales familias de herramientas.

[Novedades completas](docs/releases/v1.5.1-preview.md)

## 1.5.0-preview · Preliminar

Esta entrega refuerza la preparación y el seguimiento de las transformadas y establece un control matemático obligatorio antes de empaquetar los portables.

[Novedades completas](docs/releases/v1.5.0-preview.md)

## 1.4.2 · Estable

La versión 1.4.2 incorpora fondos transparentes y translúcidos al tema personalizado. Reúne también las mejoras de las entregas preliminares anteriores, incluidos los temas de apariencia, los controles y el zoom del plano de polos y ceros y los pares de transformadas Z y DTFT.

[Novedades completas](docs/releases/v1.4.2.md)

## 1.4.1-preview · Preliminar

Esta entrega permite editar y ampliar el plano de polos y ceros desde su propia ventana y corrige transformadas Z que quedaban pendientes después de completar una indeterminación removible.

[Novedades completas](docs/releases/v1.4.1-preview.md)

## 1.4.0-preview · Preliminar

Esta entrega amplía las opciones de apariencia y corrige el banner de inicio, que conservaba un degradado fijo al cambiar de tema. Ahora acompaña a la paleta seleccionada, incluidos los temas claros.

[Novedades completas](docs/releases/v1.4.0-preview.md)

## 1.3.1-preview · Preliminar

Esta entrega corrige la lectura del mouse en los planos de polos y ceros y permite personalizar la apariencia con cuatro temas oscuros.

[Novedades completas](docs/releases/v1.3.1-preview.md)

## 1.3.0-preview · Preliminar

Esta preliminar incorpora cursores para consultar figuras y herramientas para comparar resultados y estudiar su precisión. Las mediciones y los desarrollos explicativos se asocian a los datos realmente calculados.

[Novedades completas](docs/releases/v1.3.0-preview.md)

## 1.2.2-preview · Preliminar

Esta preliminar amplía la información de condiciones matemáticas y la comprobación de filtros, manteniendo la organización de herramientas.

[Novedades completas](docs/releases/v1.2.2-preview.md)

## 1.2.1 · Estable

La versión 1.2.1 hace visible el criterio de continuidad que ya utiliza el motor para completar singularidades removibles. La explicación permite identificar el valor añadido y distinguirlo de una condición explícita de la señal.

[Novedades completas](docs/releases/v1.2.1.md)

## 1.2.0 · Estable

La versión estable 1.2.0 consolida los flujos de Transformada Z, amplía las amplitudes por banda y permite explorar funciones de transferencia tanto en s como en z.

[Novedades completas](docs/releases/v1.2.0.md)

## 1.2.0-preview · Preliminar

Esta preliminar reúne los flujos de Z y amplía el análisis de sistemas, el diseño FIR y la importación. Describe la etapa previa a la versión estable 1.2.0.

[Novedades completas](docs/releases/v1.2.0-preview.md)

## 1.1.3 · Estable

La generación de ventanas se incorpora como operación independiente de Señales para estudiar su forma, su espectro o su Z sin diseñar primero un filtro.

[Novedades completas](docs/releases/v1.1.3.md)

## 1.1.2 · Estable

El diseño por polos y ceros incorpora un formulario de carga exacta junto a la edición gráfica. Esto permite combinar precisión numérica y exploración con el mouse.

[Novedades completas](docs/releases/v1.1.2.md)

## 1.1.1 · Estable

Las ecuaciones lineales incorporan la variante en diferencias junto a las ecuaciones diferenciales, con una carga y un informe adaptados a secuencias discretas.

[Novedades completas](docs/releases/v1.1.1.md)

## 1.1.0 · Estable

Señales Aleatorias incorpora análisis de modelos estacionarios conocidos y estimación AR desde un registro. Las propiedades teóricas y las estadísticas de una realización finita se mantienen diferenciadas.

[Novedades completas](docs/releases/v1.1.0.md)

## 1.0.2 · Estable

Los informes FIR explican cómo se obtiene la respuesta al impulso a partir del ideal y la ventana. La presentación se comparte entre el diseño por cortes y longitud y el diseño por especificaciones.

[Novedades completas](docs/releases/v1.0.2.md)

## 1.0.1 · Estable

Esta entrega aclara la interpretación de las bandas de transición FIR y mejora la representación del retardo en filtros de fase lineal.

[Novedades completas](docs/releases/v1.0.1.md)

## 1.0.0 · Estable

La primera versión estable consolida el laboratorio de señales y sistemas con herramientas independientes, una biblioteca de resultados y una calculadora simbólica.

[Novedades completas](docs/releases/v1.0.0.md)

## 0.99.11 · Preliminar

Esta preliminar histórica reúne las distintas formas de diseñar un filtro en un documento común, conservando parámetros propios para cada definición.

[Novedades completas](docs/releases/v0.99.11.md)

## 0.99.10 · Preliminar

Esta preliminar histórica organiza las transformadas de Fourier mediante una elección común de transformada, dirección y método.

[Novedades completas](docs/releases/v0.99.10.md)

## 0.99.9 · Preliminar

Esta preliminar histórica distingue los impulsos continuos ideales de las muestras ordinarias de una señal.

[Novedades completas](docs/releases/v0.99.9.md)

## 0.99.8 · Preliminar

Esta preliminar histórica amplía el envío de resultados al CAS y el reconocimiento de pares y propiedades en Z inversa.

[Novedades completas](docs/releases/v0.99.8.md)

## archivo-historico-2026-10-28 · Archivo histórico

Este archivo conserva las primeras etapas de SignalLab PC y sus ejecutables originales. Es un respaldo de consulta; para el uso habitual corresponde elegir la última versión estable.

[Novedades completas](docs/releases/archive.md)
