# Historial de cambios

Las versiones estables y preliminares se distribuyen en [GitHub Releases](https://github.com/Tincho1286/SignalLab-PC/releases). La última estable es **1.8.0 · Instalación y actualizaciones**.

## 1.8.0 · Estable · Instalación y actualizaciones

- Instaladores por usuario para Windows x64 y Linux x86_64, además de los portables.
- Búsqueda de actualizaciones desde Ayuda, descarga verificada e instalación sin desinstalar previamente.
- Conservación de temas y configuración; activación preparada y recuperación ante fallos en Linux.
- Manifiestos Ed25519, comprobación de integridad y protección frente a retrocesos de versión.

[Notas de la versión](docs/releases/v1.8.0.md)

## 1.7.0 · Estable · Mejoras de estabilidad

- Numerosas correcciones de estabilidad y fiabilidad en transformadas, sistemas, filtros y CAS.
- ROC, causalidad, condiciones iniciales y prehistoria conservadas en los resultados y comprobaciones.
- Conversión bilineal exacta, impulsos consistentes y energía FFT protegida frente a desbordamientos.
- Procedimientos registrados y reutilización de transferencias exactas en el CAS.
- Biblioteca organizada en catorce categorías, con once ejemplos y referencias cruzadas.

[Notas de la versión](docs/releases/v1.7.0.md)

## 1.6.17 · Estable · Importante

- Funciones hiperbólicas, recíprocas e inversas compartidas por todos los evaluadores.
- Ramas complejas consistentes y conservación de valores explícitos por tramos.
- Pares ordinarios de Fourier y propiedades para sinc, exponenciales y gaussianas.
- Reconocimiento de exponenciales bilaterales en Z y DTFT.
- Conservación de pares polinómicos y de cancelaciones antes de transformar.
- Ecuaciones sin memoria, reutilización de fórmulas temporales y registros mínimos válidos.

[Notas de la versión](docs/releases/v1.6.17.md)

## 1.6.16 · Preliminar

- Separación de resultados principales y gráficos, registros y mediciones complementarias.
- Conservación de fórmulas y modelos ante límites de memoria o de representación numérica.
- Normalización exacta de coeficientes y detección de componentes demasiado pequeñas para representarse.
- Conservación de resultados CAS y transformadas si falla su presentación o desarrollo explicativo.

[Notas de la preliminar](docs/releases/v1.6.16-preview.md)

## 1.6.15 · Estable

- La inversa Z separa la expresión completa de las muestras del gráfico. El modo automático admite secuencias infinitas; los desbordes de muestras conservan fórmula y ROC.
- Las ecuaciones en diferencias reconocen cancelaciones a cero antes de analizar grados polinómicos.

- Los informes de filtros muestran mínimos y máximos de cada banda de paso y rechazo, sus frecuencias y los límites permitidos.

- Presentación matemática de funciones por tramos en CAS e informes.
- Igualdades, desigualdades, valor absoluto y coordenadas periódicas legibles.
- Casos sucesivos en una tabla y tamaño de fórmula uniforme.
- Nombre de los índices k en Ventanas y resolución.

[Notas de la estable](docs/releases/v1.6.15.md)

## 1.6.14 · Preliminar

- Tablas e integrales periódicas en CAS.
- Fourier inversa por bandas y líneas espectrales, origen del período y condiciones de frecuencia.
- Escala de FFT, reloj digital y región de convergencia al cuantizar.

[Notas de la preliminar](docs/releases/v1.6.14-preview.md)

## 1.6.13 · Preliminar

- Compatibilidad de resultados, escala de convolución y correlación y reloj físico de muestreo.
- Máscaras de frecuencia, bordes en DTFT y expresión de Fourier continua inversa.
- Lectura de operaciones, matrices y rangos de MATLAB.

[Notas de la preliminar](docs/releases/v1.6.13-preview.md)

## 1.6.12 · Preliminar

- Reutilización y CAS junto al informe, con fórmulas y muestras como resultados separados.
- Dominios discretos y continuos en CAS, inversas de bandas con retardo y respuestas temporales coherentes con sus datos.
- Validación de ROC en precisión finita y de integrales bilaterales divergentes.

[Notas de la preliminar](docs/releases/v1.6.12-preview.md)

## 1.6.11 · Hotfix

- Actualización del CAS para DTFT algebraica, filtros ideales y resultados reimportados.

- Fórmulas en los informes de respuesta temporal, con recurrencias y condiciones iniciales para sistemas discretos.
- Expresión de la respuesta al impulso en filtros por tramos e inversas de Fourier con un informe del resultado calculado.
- Ajustes de validación y reutilización de datos entre herramientas.

[Notas de la entrega](docs/releases/v1.6.11.md)

## 1.6.10 · Hotfix

- Dominio y variables ligadas en el CAS, validación de entradas y reutilización de transferencias Laurent.
- Ejes importados, operaciones de MATLAB, relojes y compatibilidad entre resultados.
- Conversiones de filtros, precisión de Fourier, cuantización e índices de gráficos.

[Notas de la entrega](docs/releases/v1.6.10.md)

## 1.6.9 · estable

- Dominios, exclusiones y supuestos conservados al operar y resolver en el CAS.
- Condiciones por tramos, sustitución en listas, conversión de matrices y reutilización segura de respuestas en frecuencia.
- Escalado previo a la FFT en la STFT.
- Correcciones de las preliminares 1.6.6 a 1.6.8 incluidas en la entrega estable.

[Notas de la entrega](docs/releases/v1.6.9.md)

## 1.6.8 · preliminar

- Cancelaciones exactas y límites impares en Z inversa por contorno.
- Energía por bins de DFT, conservación del eje de Fourier continua y validación de líneas espectrales.
- Escalado en PSD, normalización de ganancia y varianza con divisor N−1.
- Dominio correcto al enviar señales a Hilbert y STFT, validación de ejes en productos y diagnóstico portable actualizado.

[Notas de la entrega](docs/releases/v1.6.8-preview.md)

## 1.6.7 · preliminar

- Fase precisa en la DTFT inversa y validación de las entradas de Fourier inversa.
- Extremos del producto continuo, carga en el editor y campos del periodograma según el método.
- Validación de la ROC para compensación FIR y reloj en convolución por bloques.
- Escalado seguro en Hilbert, cuantización de rangos amplios y reconstrucción con eje físico independiente.

[Notas de la entrega](docs/releases/v1.6.7-preview.md)

## 1.6.6 · preliminar

- Selección correcta de la entrada reutilizada en Densidad de energía y conservación del reloj en convolución, PSD y edición de ejes.
- Cancelaciones exactas al exportar canales de espacio de estados y al simular transferencias continuas desde reposo.
- Conservación de una ROC compatible en cascadas y sumas.
- Filtrado en frecuencia sobre rejillas completas y manejo preciso de índices discretos grandes.
- Reapertura de CSV propios con el paso declarado.

[Notas de la entrega](docs/releases/v1.6.6-preview.md)

## 1.6.5 · estable

- La DFT directa permite elegir frecuencia angular o índice k centrado en el gráfico y la tabla.
- DFT directa centrada en rad/muestra y superposición DTFT opcional en el estudio de ventanas.
- Kaiser busca la longitud FIR mínima que cumple las tolerancias cuando la longitud está en modo automático.
- El informe distingue la longitud elegida de la estimación por fórmula.

[Notas de la entrega](docs/releases/v1.6.5.md)

## 1.6.3 · preliminar

- Longitud FIR automática para ventanas distintas de Kaiser en el diseño por bandas.
- Cálculo FIR más rápido y escala vertical ajustable por panel en los gráficos.
- Validación de la ROC al convertir a espacio de estados y límites de frecuencia por canal.
- Reloj conservado al reutilizar la salida del filtrado en frecuencia.

[Notas de la entrega](docs/releases/v1.6.3-preview.md)

## 1.6.2 · preliminar

- Intersección correcta de las ROC y Z inversa de sumas racionales y logarítmicas.
- Conversión por invarianza al impulso con ROC y simulación desde reposo con cancelaciones exactas.
- Fase de sistemas racionales, bin de Nyquist y orígenes grandes en DTFT/DFT.

[Notas de la entrega](docs/releases/v1.6.2-preview.md)

## 1.6.1 · preliminar

- Validación de la ROC en simulaciones causales y cancelación exacta en cascadas.
- Energía de secuencias con soporte definido y magnitud en dB para ganancias extremas.
- Reapertura de figuras sin duplicar registros y Z inversa de series recíprocas.

[Notas de la entrega](docs/releases/v1.6.1-preview.md)

## 1.6.0 · estable

- Acceso uniforme a las figuras desde la cabecera de resultados e informes en todas las herramientas.
- Selección de figuras disponibles desde un único botón cuando hay varias vistas.
- Fourier/DTFT algebraicas y medidas de energía/potencia con apertura de gráficos junto a sus informes.
- Integración de las mejoras de transformadas, indeterminaciones, rango numérico y conservación de condiciones desarrolladas en la serie 1.5.
- Portables para Windows x64 y Linux x86_64.

[Notas de la entrega](docs/releases/v1.6.0.md)

## 1.5.10 · preliminar

- Polos periódicos y evaluaciones mal condicionadas marcados como N/D.
- Razones de polinomios y cascadas revisadas ante desbordamientos intermedios.
- Valores fuera del rango numérico diferenciados de ceros exactos.
- Retardo de grupo y exportaciones coherentes con las posiciones disponibles.
- Validación del soporte activo de secuencias con escalones e impulsos.

[Notas de la entrega](docs/releases/v1.5.10-preview.md)

## 1.5.9 · preliminar

- Nombres de impulsos y escalones compartidos entre los dominios continuo y discreto.
- Valores por continuidad conservados antes de aplicar impulsos o escalones.
- ROC, período y definición original conservados en reescrituras equivalentes del CAS.
- Región de convergencia trasladada a las inversas, con selección explícita cuando falta.

[Notas de la entrega](docs/releases/v1.5.9-preview.md)

## 1.5.8 · preliminar

- Impulsos discretos reconocidos por Z y DTFT, incluidos desplazamientos y soporte efectivo.
- Pares básicos de Fourier e inversa para constantes, polinomios y exponenciales.
- Factores de escala de las derivadas de Dirac conservados en Laplace.

[Notas de la entrega](docs/releases/v1.5.8-preview.md)

## 1.5.7 · preliminar

- Presentación de la DTFT de la sinc bilateral sin confundirla con la sumatoria formal de Z.
- Unidades y restricciones de frecuencia conservadas al reutilizar resultados en CAS y análisis H(w).
- Gráficas condicionadas con posiciones N/D preservadas en tabla y exportación.
- Ejes MATLAB int64 exactos y rechazo de ejes o canales incompatibles.
- Apertura de CSV propios descendentes y validación de JSON/metadatos sin incorporación parcial.

[Notas de la entrega](docs/releases/v1.5.7-preview.md)

## 1.5.6 · preliminar

- Filtros ideales escritos con step: retardo ordinario por tramos y exclusión de saltos.
- Diagnóstico visible de errores inesperados en botones y trazas locales de cálculos fallidos.
- Estado terminal correcto tras un fallo de presentación y descarte de notificaciones duplicadas.
- Control estático de nombres y de importaciones locales condicionales antes del empaquetado.

[Notas de la entrega](docs/releases/v1.5.6-preview.md) · [Mejoras de fiabilidad](docs/maintenance.md)

## 1.5.5 · preliminar

- Análisis de DTFT como H(exp(iw)) aunque Z no tenga un anillo abierto de convergencia absoluta.
- Entrada de respuesta H(w), reutilización desde Resultados y exportación/apertura de definiciones.
- Retardo de grupo excluido en saltos y respuestas nulas; fase de sinc con centros fraccionarios.
- Corrección del botón Graficar resultado de Fourier algebraica y apertura explícita de la figura.
- Nueve recorridos Qt y 76 controles matemáticos de referencia obligatorios, además del barrido preventivo.

[Notas de la preliminar](docs/releases/v1.5.5-preview.md)

## 1.5.4 · preliminar

- Análisis de transferencias no racionales como expresiones, sin forzar coeficientes b/a.
- Conservación de la secuencia, soporte y condiciones al enviar X(z) al análisis de H(z).
- Reutilización desde Resultados, importación y archivos JSON de definición.
- Frecuencia, fase y retardo para H(s)/H(z) generales, con límites separados de valores y derivadas.
- Seis recorridos de interfaz obligatorios, además de 74 controles matemáticos y el barrido preventivo.

[Notas de la preliminar](docs/releases/v1.5.4-preview.md)

## 1.5.3 · preliminar

- Barrido preventivo obligatorio con una base fija y variaciones reproducibles derivadas del código.
- Registro de parámetros, referencias y plazos por caso; bloqueo de construcción ante fallos o cálculos incompletos.
- DTFT unilateral con convergencia ordinaria comprobada independientemente de la ROC abierta de Z.
- Límites de retardo de grupo coherentes con la respuesta para factores comunes exactos.
- Informes públicos: 69 controles de referencia y 112 casos de barrido en ambas plataformas.

[Notas de la preliminar](docs/releases/v1.5.3-preview.md)

## 1.5.2 · preliminar

- Normalización de factores antes de reconocer pares Z desplazados.
- Pares de potencias recíprocas con centros fraccionarios mediante Lerch.
- Sinc/rectángulo con fase conservada, formas seno/coseno e imágenes espectrales.
- Control por propiedades de escalas, desplazamientos, soportes y muestras explícitas; 63 pruebas obligatorias.

[Notas de la preliminar](docs/releases/v1.5.2-preview.md)

## 1.5.1 · preliminar

- Analizador común de constantes exactas, campos numéricos y coeficientes.
- Validación de enteros, dominios de funciones y pérdida de coeficientes al normalizar filtros.
- Entradas de ecuaciones coherentes con las transformadas y reconocimiento de sinc como impulso en recurrencias.
- Ventanas compartidas entre señales, FIR por h[n] y estimación espectral.
- Control obligatorio ampliado a 56 pruebas en nueve familias matemáticas.

[Notas de la preliminar](docs/releases/v1.5.1-preview.md) · [Fiabilidad matemática](docs/mathematical-reliability.md)

## 1.5.0 · preliminar

- Definición matemática conservada con expresión exacta, dominio, soporte y notas de continuidad.
- Preparación común de Z y DTFT y tratamiento de valores aislados en integrales ordinarias.
- Corrección de inversas constantes y factores racionales cancelables en Laplace.
- Estados de cálculo coherentes y procedencia conservada al enviar resultados al CAS.
- Control permanente de 21 pruebas; los constructores Windows/Linux se detienen ante un fallo.

[Notas de la preliminar](docs/releases/v1.5.0-preview.md) · [Fiabilidad matemática](docs/mathematical-reliability.md)

## 1.4.2

- Fondos Opaco, Translúcido y Transparente en el tema personalizado.
- Opacidad de menús de 0 a 100 %, independiente de la intensidad de la foto.
- Foto continua detrás de tarjetas, categorías y navegación, sin desvanecer textos ni botones.
- Vista previa actualizada y opciones desplazables en el diálogo de apariencia.
- Preferencias anteriores conservadas con fondo inicialmente opaco.

[Notas de la versión](docs/releases/v1.4.2.md) · [Configurar apariencia](docs/appearance.md)

## 1.4.1 · preliminar

- Selección de polo/cero, conjugados y coordenadas dentro de la ventana del plano.
- Zoom con rueda y botones, encuadre de raíces y conservación de la escala al editar.
- Transformada Z por pares y propiedades, separando los valores completados por continuidad.
- Par sinc/rectángulo en DTFT y distinción explícita frente a una ROC vacía de Z.
- Reutilización de condiciones por tramos y ayudas actualizadas.

[Notas de la preliminar](docs/releases/v1.4.1-preview.md) · [Transformada Z y sinc](docs/z-transforms.md)

## 1.4.0 · preliminar

- Banner de inicio adaptado a la paleta seleccionada.
- Temas Vanta Black, Rosa, Claro y Blanco, además de los cuatro anteriores.
- Tema personalizado con base, acento y foto local; vista previa, intensidad y encuadre.
- Iconos y fórmulas adaptados a fondos claros y oscuros, conservando datos y zoom.

[Notas de la preliminar](docs/releases/v1.4.0-preview.md) · [Configurar apariencia](docs/appearance.md)

## 1.3.1 · preliminar

- Coordenadas libres en los planos de polos y ceros, sin ajuste al círculo unitario.
- Cursor × para insertar polos y ○ para insertar ceros, centrados en el punto de inserción.
- Cuatro temas oscuros desde Vista → Tema, con elección persistente.
- Actualización de informes y figuras abiertas conservando datos y zoom.

[Notas de la preliminar](docs/releases/v1.3.1-preview.md) · [Temas](docs/appearance.md)

## 1.3.0 · preliminar

- Cursores A/B enlazados, lectura de muestras originales y copia de mediciones.
- Comparación de señales y sistemas desde Resultados, con coordenadas y condiciones preservadas.
- Diagnóstico de sensibilidad en el estudio de precisión de coeficientes.
- Residuos de ecuaciones y comprobación de condiciones iniciales de EDO.
- Desarrollo opcional en Fourier, convolución y ecuaciones; ayuda de cursores accesible en las herramientas.

[Notas y alcance](docs/releases/v1.3.0-preview.md) · [Guía de cursores](docs/cursors.md)

## 1.2.2 · preliminar

- Condiciones matemáticas reunidas y ROC analógica preservada en reutilización y exportación.
- Extremos de filtros refinados, frecuencias de mínimos/máximos y margen frente a tolerancias.
- Desarrollo opcional registrado para Z y Laplace, separado del resultado principal.
- Errores de entrada contextualizados, con señalización del campo y conservación del texto.
- Propuestas de consolidación en [la hoja de mejoras](docs/roadmap.md).

[Notas y alcance](docs/releases/v1.2.2-preview.md)

## 1.2.1 · 2026-11-02

- Aviso visible en el editor y explicación en la ayuda de cada herramienta.
- Informe con puntos y valores exactos de las indeterminaciones removibles completadas por continuidad; indicación en la barra de estado.
- Conservación del detalle en Resultados y exportación de informes, con traslado de los avisos desde el proceso simbólico.
- Portables Windows y Linux; se conserva el criterio matemático existente y los valores definidos por tramos.

## Distribución Linux · 2026-11-02

- Portable nativo Linux x86_64 incorporado a la versión estable 1.2.0.
- Paquete TAR con ejecutable, licencias, instrucciones y procedencia; no requiere instalar Python.
- Construcciones Windows y Linux en GitHub Actions por defecto, con dependencias específicas de plataforma.

## Documentación y licencia · 2026-11-02

- Publicación del código y los recursos originales bajo GPL-3.0-or-later.
- Texto íntegro de licencia, alcance, metadatos del paquete y avisos originales de dependencias.
- Fuentes y avisos accesibles junto a la descarga 1.2.0; el ejecutable y sus cálculos se conservan.

## 1.2.0 — Transferencias H(s)/H(z) y vistas por componentes

- Ajuste de fase con sistemas y complementos explícitos: fase mínima, pasa todo y construcción de fase lineal con sus condiciones de módulo, causalidad y ROC.

- Representación de H(s) y H(z) mediante mallas de parte real/imaginaria o módulo/ángulo, con expresión asociada.
- Elección de componentes también en la respuesta en frecuencia, conservando retardo de grupo.
- Consolidación de Z, límites removibles, amplitudes por banda e importación compartida.
- Ayuda actualizada y explicación de las alertas de firma y reputación de Windows.

[Notas y alcance](docs/releases/v1.2.0.md) · [Descargar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.2.0)

## 1.2.0-preview — Z integrada, plano complejo y amplitudes por banda

La próxima versión reúne los flujos de Transformada Z y amplía el análisis de sistemas, el diseño FIR y la importación de datos.

- Transformada Z organizada en Directa e Inversa. Las secuencias finitas se cargan dentro de la directa; la inversa puede recuperar el soporte completo de un polinomio de Laurent.
- Envío a CAS y análisis de X(z) como H(z) en los flujos de Z, conservando expresiones, índices, reloj y contexto de convergencia compatible.
- Tratamiento compartido de singularidades removibles mediante límites exactos. La sinc normalizada conserva sinc(0)=1, también con desplazamientos y escalas.
- Nueva vista de H(z) en el plano complejo: mapa de módulo, polos, ceros, círculo unitario y ROC. La respuesta en frecuencia se estudia por separado.
- Amplitudes configurables en las bandas de paso y dos amplitudes independientes para el rechazabanda FIR. Tolerancias absolutas, relativas o en dB.
- Importación de archivos y reutilización de resultados desde entradas compatibles, con carga independiente por operando. Nuevas explicaciones e ilustraciones en la ayuda.

[Notas y alcance](docs/releases/v1.2.0-preview.md) · [Descargar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.2.0-preview)

## 1.1.3 — Ventanas como señales independientes

Generación de ventanas para estudiar su forma, su espectro y su transformada Z sin diseñar antes un filtro.

- Señales → Crear una señal → Ventana: rectangular, Hann, Hamming, Blackman, Bartlett y Kaiser, en sus variantes simétricas.
- Longitud total L, índice inicial o centrado alrededor de cero; parámetro β para Kaiser.
- Gráfico discreto de tallos, tabla e informe de la ventana. Exportación JSON/CSV y reutilización en Fourier, Z y producto de señales.
- Conservación de los ceros exactos de los extremos de Hann, Bartlett y Blackman; evaluación estable de Kaiser para valores elevados de β.
- Envío de secuencias a Z con su origen e índices completos y ayuda ilustrada sobre longitud y centrado.

[Notas y alcance](docs/releases/v1.1.3.md) · [Descargar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.1.3)

## 1.1.2 — Carga exacta de polos y ceros

Un formulario dedicado permite agregar y editar raíces con precisión, junto al diseño interactivo con el mouse.

- Carga de polos y ceros en forma binómica o polar, con ángulo en radianes.
- Admite fracciones, pi, constantes y potencias como 10^(-3), conservando las expresiones ingresadas.
- Lista editable por filas, selección múltiple y eliminación de raíces individuales.
- Adición opcional del conjugado y conservación de multiplicidades; una raíz real no se duplica automáticamente.
- Coordenadas exactas sobre los ejes para múltiplos de pi/2 y conservación de las expresiones al editar otros puntos con el mouse.
- Ayuda ilustrada sobre partes real/imaginaria, módulo, ángulo y conjugados.

[Notas y alcance](docs/releases/v1.1.2.md) · [Descargar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.1.2)

## 1.1.1 — Ecuaciones en diferencias

Las ecuaciones lineales incorporan una variante discreta junto al cálculo de ecuaciones diferenciales.

- Resolución de a₀y[n]+a₁y[n−1]+…+aₚy[n−p]=f[n] con coeficientes constantes.
- Entrada por fórmula o tramos, índice inicial y reposo o historial de salida anterior.
- Solución algebraica legible en n, respuesta de entrada cero y de estado cero, con muestras para gráfico y tabla.
- Transferencia H(z) bajo condiciones iniciales nulas, separada de la solución que incluye el historial.
- Reutilización de expresiones en CAS y otras herramientas, con ayuda específica sobre el orden de los datos.

[Notas y alcance](docs/releases/v1.1.1.md) · [Descargar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.1.1)

## 1.1.0 — Modelos AR, MA y ARMA

Las herramientas de señales aleatorias incorporan modelos estacionarios conocidos y estimación AR desde registros.

- Media, varianza, potencia, autocovarianza, autocorrelación y PSD teóricas de modelos discretos AR/MA/ARMA.
- Realizaciones gaussianas con estado inicial estacionario y semilla reproducible.
- Estimación AR mediante Yule–Walker con orden elegido, innovación estimada, espectro y residuo.
- Correlación y covarianza auto/cruzada con alineación por índices, normalización y conjugación de datos complejos.
- Transferencias, curvas y registros reutilizables en sistemas, Resultados y CAS, con ayuda ilustrada.

[Notas y alcance](docs/releases/v1.1.0.md) · [Descargar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.1.0)

## 1.0.2 — Expresiones del ideal y del FIR enventanado

Los informes FIR muestran cómo se obtiene la respuesta al impulso del filtro a partir del ideal y la ventana.

- Expresiones textbook de h_ideal[n], el núcleo continuo g(x), la ventana w[n] y la respuesta final h[n].
- Longitud L, orden nominal M=L−1 y desplazamiento D=(L−1)/2, también para longitudes pares.
- Fórmulas compartidas entre el diseño por cortes/longitud y por especificaciones.
- La ganancia indicada corresponde al factor realmente aplicado a los coeficientes.

[Notas y alcance](docs/releases/v1.0.2.md) · [Descargar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.0.2)

## 1.0.1 — Transiciones FIR y retardo de grupo

Se aclara el significado de las transiciones especificadas y se mejora la representación del retardo de fase lineal.

- Identificación separada de los anchos de transición izquierdo y derecho a partir de los bordes ingresados.
- Informe de los cortes ideales y de la transición más estrecha usada para estimar la longitud Kaiser.
- Aclaración de que las franjas del gráfico representan intervalos permitidos y no el ancho medido de la curva.
- Retardo exacto para FIR reales con simetría o antisimetría exacta, manteniendo los puntos no definidos.

[Notas y alcance](docs/releases/v1.0.1.md) · [Descargar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.0.1)

## 1.0.0 — Primera versión estable

Base estable del laboratorio de señales y sistemas, con herramientas independientes, resultados reutilizables y CAS.

- Organización de 29 herramientas agrupadas y 80 variantes, además de la calculadora simbólica.
- Diseño unificado de filtros y análisis separado de funciones de transferencia, respuestas, raíces y realizaciones.
- Entradas locales, biblioteca de resultados, importación/exportación, gráficos externos y ayuda contextual ilustrada.
- Corrección de avisos de datos modificados en los diseños RC/FIR y conservación de cambios realizados durante un cálculo.
- Identificación de versión, documentación de alcance y distribución portable para Windows.

[Notas y alcance](docs/releases/v1.0.0.md) · [Descargar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v1.0.0)

## 0.99.11 — Diseño de filtros unificado

Las distintas formas de definir un filtro se reúnen en un mismo documento con parámetros propios.

- Diseño por especificaciones FIR/IIR, cortes, h[n], raíces, segundo orden y RC desde una entrada común.
- Dominio y estructura aparecen cuando aportan una elección; cada formulario conserva sus valores.
- Análisis, reutilización y exportación junto al resultado calculado, incluyendo filtro JSON y respuesta CSV.
- Formularios más despejados y ayuda en colores para relacionar cada definición con el filtro obtenido.

[Notas y alcance](docs/releases/v0.99.11.md) · [Descargar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v0.99.11)

## 0.99.10 — Fourier y navegación por variantes

La elección de transformada, dirección y cálculo se presenta con una estructura común.

- DTFT, DFT/FFT y Fourier continua organizadas por transformada, dirección y método de cálculo.
- Conservación de la dirección inversa al cambiar entre modelos compatibles.
- Búsqueda por variantes y navegación consistente hacia la operación correspondiente.
- Preparación de entradas compatibles sin mezclar definiciones de naturaleza diferente.

[Notas y alcance](docs/releases/v0.99.10.md) · [Descargar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v0.99.10)

## 0.99.9 — Señales continuas e impulsos ideales

La carga de señales continuas conserva por separado la parte ordinaria y los pesos de impulsos Dirac.

- Posiciones y pesos de impulsos ideales, incluso entre puntos de la rejilla temporal.
- Contribuciones de Dirac en Fourier continua, series, convolución y respuesta de sistemas compatibles.
- Conservación de impulsos y metadatos en JSON/CSV y al reutilizar los datos en CAS.
- Distinción entre impulso continuo ideal y muestra discreta, con rechazo de operaciones distributivas ambiguas.

[Notas y alcance](docs/releases/v0.99.9.md) · [Descargar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v0.99.9)

## 0.99.8 — Resultados en CAS e inversa Z por propiedades

La reutilización de resultados incorpora el CAS y la inversa Z reconoce pares y desplazamientos antes de la descomposición general.

- Envío de expresiones, sistemas, señales, modelos de estado y datos calculables a una hoja CAS existente.
- Conservación de variables, borradores y supuestos; los resultados importados quedan referenciados como rN.
- Reconocimiento de linealidad, pares geométricos, polos repetidos y desplazamientos enteros en la inversa Z.
- Fórmulas más compactas con sus condiciones y ROC, preservando definiciones algebraicas exactas cuando están disponibles.

[Notas y alcance](docs/releases/v0.99.8.md) · [Descargar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v0.99.8)

## Archivo histórico — primeras versiones

Respaldo de las primeras etapas de SignalLab PC y sus ejecutables originales.

- 112 ejecutables distintos reunidos en un archivo TAR.ZST de aproximadamente 222 MiB.
- Primer portable v0.1.0 y su respaldo de código fuente disponibles como adjuntos separados.
- Manifiesto con versiones, rutas relativas, tamaños y hashes SHA-256 para identificar los archivos.
- Guía de recuperación y verificación incluida con el archivo histórico.

[Notas y alcance](docs/releases/archive.md) · [Descargar](https://github.com/Tincho1286/SignalLab-PC/releases/tag/archivo-historico-2026-10-28)
