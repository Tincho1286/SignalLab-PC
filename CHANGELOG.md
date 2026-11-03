# Historial de cambios

Las versiones estables y preliminares se distribuyen en [GitHub Releases](https://github.com/Tincho1286/SignalLab-PC/releases). La última estable es **1.2.1**.

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
