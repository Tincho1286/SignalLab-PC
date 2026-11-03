# Inventario de menús y opciones HP

> Inventario histórico parcial. El inventario reproducible actual está en `INVENTARIO_REPRODUCIBLE_HP.md`: incluye títulos calculados y distingue concatenaciones de opciones. Por ejemplo, «Aplicar intervalo SNR» contiene dos opciones, no tres. Los números de esta lista se conservan para no romper referencias históricas.

Extraído del fuente completo de referencia `references/SignalLab_App_5.0.hppl` mediante las llamadas literales `SSMenu(título, {opciones})`. Incluye opciones exactas estáticas y menús repetidos cuando aparecen en rutas distintas. Los menús construidos dinámicamente y opciones generadas concatenando datos se identifican como tales; revisar la función UI indicada en el código antes de portarlos.

Se revisaron 10.407 líneas. Las ocho entradas del tablero y opciones principales están en `MATRIZ_MIGRACION.md`. Categorías: datos y ejes, navegación, generación/edición, transformadas, Fourier, muestreo, filtros/control, teoría y resultados.

## 1. Interpretar datos
- 1. Conservar origen y paso
- 2. Solo valores; indice desde cero
- 3. Cancelar

## 2. Destino de exportacion
- 1. Banco SignalLab (menos memoria)
- 2. Listas Home L0 y L1
- 3. Tabla Home M0
- 4. Banco + L0 + L1 + M0
- 5. Guardar en historial
- 6. Cancelar

## 3. Fuente de datos
- 1. Ingresar una lista
- 2. Usar banco SignalLab
- 3. Usar lista L0 de Home

## 4. Fuente de datos
- 1. Ingresar una lista
- 2. Usar lista L0 de Home

## 5. Lista L0 de Home
- 1. Usar valores e indice desde cero
- 2. Asociar eje uniforme de L1
- 3. Cancelar

## 6. Calculo guardado
- 1. Reabrir resultado / editar
- 2. Consultar datos guardados
- 3. Volver a Recientes

## 7. Senal guardada
- 1. Ver datos y eje
- 2. Ver tabla
- 3. Reutilizar como banco
- 4. Volver

## 8. Lecturas del grafico
- 1. Valor del punto actual B
- 2. Fijar este punto como A
- 3. Medir de A a B
- 4. Borrar referencia A
- 5. Contexto del grafico
- 6. Volver

## 9. Formula y condiciones
- 1. Formula Textbook
- 2. Limites y condiciones
- 3. Expresion lineal completa
- 4. Continuar al integrando
- 5. Volver

## 10. Antes de salir
- 1. Guardar en Recientes y salir
- 2. Salir sin guardar
- 3. Seguir en el resultado

## 11. Acciones del grafico
- 1. Tabla completa
- 2. Lectura del cursor
- 3. Activar/desactivar cursor
- 4. Original / limpia
- 5. Autoescala
- 6. Volver al grafico

## 12. Acciones del grafico
- 1. Tabla completa
- 2. Lectura del cursor
- 3. Activar/desactivar cursor
- 4. Original / limpia
- 5. Autoescala
- 6. Volver al grafico

## 13. Acciones de comparacion
- 1. Tablas
- 2. Mostrar/ocultar contraria
- 3. Original / limpia
- 4. Autoescala
- 5. Volver al grafico

## 14. Acciones de comparacion
- 1. Tablas
- 2. Original / limpia
- 3. Autoescala
- 4. Volver al grafico

## 15. Datos de la comparacion
- 1. DTFT: tabla compleja
- 2. DFT: tabla compleja
- 3. Volver al grafico

## 16. Acciones de comparacion
- 1. Tablas
- 2. Mostrar/ocultar contraria
- 3. Original / limpia
- 4. Autoescala
- 5. Volver al grafico

## 17. Acciones de comparacion
- 1. Tablas
- 2. Original / limpia
- 3. Autoescala
- 4. Volver al grafico

## 18. Cambios del filtro
- 1. Guardar en Recientes y volver
- 2. Descartar cambios
- 3. Seguir editando

## 19. Posicionar polos y ceros
- 1. Agregar cero en cursor
- 2. Agregar polo en cursor
- 3. Cero y su conjugado
- 4. Polo y su conjugado
- 5. Mover un cero al cursor
- 6. Mover un polo al cursor
- 7. Eliminar un cero
- 8. Eliminar un polo
- 9. Coordenadas exactas del cursor
- 10. Cambiar paso de las flechas
- 11. Guardar y volver
- 12. Volver al plano
- 13. Autoescala
- 14. Agregar por coordenadas
- 15. Ver H(z) del diseno

## 20. Agregar por coordenadas
- 1. Polo
- 2. Cero
- 3. Volver

## 21. Modulacion
- 1. exp(i*(w0*X+phi))
- 2. cos(w0*X+phi)
- 3. sin(w0*X+phi)
- 4. Volver

## 22. Indice n desde 0
- 1. Tabla por indice
- 2. Grafico por indice
- 3. Exportar con indice n
- 4. Volver

## 23. Salida: eje t en segundos
- 1. Tabla con tiempo
- 2. Grafico con tiempo
- 3. Exportar con tiempo
- 4. Volver

## 24. Unidad de frecuencia de corte
- 1. fc en ciclos/muestra
- 2. wc en radianes/muestra
- 3. Cancelar

## 25. IIR: confirmar advertencia
- 1. Cancelar cambio
- 2. Aplicar para analisis teorico

## 26. Comparar filtro ideal
- 1. Muestras sin/con filtro
- 2. Curva SINC de la salida
- 3. Volver

## 27. Consultar filtro IIR
- 1. Funcion H(z)
- 2. Numerador b[k]
- 3. Denominador a[k]
- 4. Estado y convenciones
- 5. Volver

## 28. Consultar filtro ideal
- 1. Respuesta H y contexto
- 2. Formula de h[k]
- 3. Nucleo h[k] para k >= 0
- 4. Volver

## 29. Espectros por etapa
- 1. Original x[n]
- 2. Salida sin filtro opcional
- 3. Salida final y[n]
- 4. Volver

## 30. Vistas del resultado
- 1. Magnitud
- 2. Fase (rad)
- 3. Parte real
- 4. Parte imaginaria
- 5. Volver

## 31. Formula y eje
- 1. Formula del registro Textbook
- 2. Unidades y convenciones
- 3. Volver

## 32. Eje y unidades
- 1. Indice n / frecuencia original
- 2. Bins k centrados (DFT/serie)
- 3. Hz / segundos: indicar Ts
- 4. Volver

## 33. Analisis de fase
- 1. Fase desenrollada
- 2. Retardo de grupo (muestras)
- 3. Volver

## 34. Metodo / offset
- 1. Redondeo sin offset
- 2. Truncamiento sin offset
- 3. Redondeo: nivel cero
- 4. Truncamiento: nivel cero
- 5. Cancelar

## 35. Intervalo para SNR
- 1. Registro completo
- 2. Por indices n (desde 0)
- 3. Por eje original (t o n)
- 4. Volver

## 36. Aplicar intervalo SNR
- 1. Aplicar: 
- 2.  muestras
- 3. Cancelar; conservar anterior

## 37. Generador discreto
- 1. Impulso
- 2. Escalon
- 3. Rampa
- 4. Exponencial
- 5. Seno
- 6. Pulso rectangular
- 7. Expresion matematica x[n]

## 38. Expresion o tramos
- 1. Muestrear expresion x(t)
- 2. Tramos continuos x(t)
- 3. Tramos discretos x[n]
- 4. Volver

## 39. Editar senal sin recargar
- 1. Expresion o un tramo
- 2. Origen de la ventana
- 3. Paso Ts (continuo)
- 4. Cantidad de puntos N
- 5. Valor exterior (tramos)
- 6. Volver al resultado

## 40. Operacion con secuencias
- 1. Desplazar x[n-k]
- 2. Invertir x[-n]
- 3. Escalar amplitud
- 4. Sumar otra senal
- 5. Partes par e impar

## 41. Dominio de energia teorica
- 1. Discreta: x[n]
- 2. Continua: x(t)
- 3. Volver

## 42. Energia y potencia
- 1. Lista discreta finita
- 2. Expresion discreta por indices
- 3. Expresion continua por intervalo
- 4. Analisis teorico en todo el eje
- 5. Formulas y clasificacion
- 6. Densidad espectral de energia
- 7. Volver

## 43. Senales continuas y discretas
- 1. Crear secuencia x[n]
- 2. Crear expresion o senal por tramos
- 3. Transformar o sumar secuencias
- 4. Calcular energia y potencia
- 5. Conceptos y clasificacion
- 6. Volver al inicio

## 44. Correlacion y autocorrelacion
- 1. Autocorrelacion discreta
- 2. Correlacion cruzada discreta
- 3. Autocorrelacion continua
- 4. Correlacion cruzada continua
- 5. Auto periodica discreta
- 6. Auto periodica continua
- 7. Volver

## 45. Modelo de correlacion discreta
- 1. Lineal: registro finito
- 2. Circular: un periodo
- 3. Volver

## 46. Formula de correlacion
- 1. Definicion y escala
- 2. CAS sin normalizar: todo el eje
- 3. Volver

## 47. Entradas utilizadas
- 1. Primera entrada x
- 2. Segunda entrada h
- 3. Volver

## 48. Escala de correlacion
- 1. Integral de un periodo
- 2. Normalizada: R(tau)/R(0)
- 3. Promedio de periodo: r/T
- 4. Volver

## 49. Escala de correlacion
- 1. Sin normalizar: suma
- 2. Coeficiente r/sqrt(Ex*Eh)
- 3. Promedio de periodo: r/L
- 4. Volver

## 50. Escala de correlacion
- 1. Sin normalizar: suma/integral
- 2. Coeficiente r/sqrt(Ex*Eh)
- 3. Volver

## 51. Entrada del sistema
- 1. Impulso
- 2. Escalon

## 52. Polos, ceros y filtros
- 1. Analizar / editar coeficientes
- 2. Disenar ubicando polos y ceros
- 3. Volver

## 53. Dominio de estabilidad
- 1. Continuo: plano s
- 2. Discreto: plano z

## 54. Respuesta del diseno
- 1. Magnitud |H(e^jw)|
- 2. Fase en radianes
- 3. Magnitud en dB
- 4. Volver

## 55. Coeficientes del filtro
- 1. Tabla numerador b[k]
- 2. Tabla denominador a[k]
- 3. Exportar b[k]
- 4. Exportar a[k]
- 5. Volver

## 56. Aplicar el diseno actual
- 1. Continuar con esta H(z)
- 2. Cancelar

## 57. Sistemas LTI
- 1. Convolucion discreta x[n]*h[n]
- 2. Convolucion continua numerica
- 3. Correlacion y autocorrelacion
- 4. Resolver ecuacion en diferencias
- 5. Respuesta a impulso o escalon
- 6. Polos, ceros y estabilidad
- 7. Conceptos y propiedades LTI
- 8. Volver al inicio

## 58. Transformada Z
- 1. Secuencia finita con indices
- 2. Expresion CAS y graficos
- 3. Simbolica: tablas y CAS
- 4. Volver

## 59. Bilineal sin resultado
- 1. Editar H(s)
- 2. Editar T
- 3. Volver

## 60. Modo de Fourier continua
- 1. Numerico: graficos y tablas
- 2. Simbolico: tablas y CAS
- 3. Volver

## 61. Entrada serie continua
- 1. Expresion x(t)
- 2. Tren de pulsos rectangulares
- 3. Tren de impulsos Dirac
- 4. Volver

## 62. Entrada B + tren Dirac
- 1. Nivel continuo B
- 2. Impulsos: posiciones y areas
- 3. Volver

## 63. Editar tren periodico
- 1. Periodo T
- 2. Altura o area A
- 3. Offset vertical B
- 4. Ancho (solo pulsos)
- 5. Centro temporal
- 6. Armonicos K
- 7. Volver al resultado

## 64. Fourier cancelada
- 1. Reintentar: misma entrada
- 2. Volver sin calcular

## 65. Inversa cancelada
- 1. Reintentar: mismo espectro
- 2. Volver sin calcular

## 66. Formula de Fourier
- 1. Completa: tablas y CAS
- 2. Integral de la ventana (CAS)
- 3. Formula numerica de los graficos
- 4. Volver

## 67. Formulas de la serie
- 1. Suma parcial explicita xK(t)
- 2. Coeficiente general c[k] (CAS)
- 3. Valor medio c[0] numerico
- 4. Volver

## 68. Editar serie por expresion
- 1. Expresion x(t) con X
- 2. Periodo T
- 3. Armonicos K
- 4. Precision N
- 5. Volver al resultado

## 69. Transformadas Laplace y Z
- 1. Laplace directa: x(t) a X(s)
- 2. Laplace inversa: X(s) a x(t)
- 3. Transformada Z de secuencia
- 4. Z inversa: X(z) a x[n]
- 5. Resolver una EDO simbolica
- 6. Bilineal: H(s) a H(z)
- 7. Teoria, convergencia y ROC
- 8. Volver al inicio

## 70. Fourier discreta
- 1. DFT directa
- 2. DFT inversa
- 3. DTFT de expresion o lista finita
- 4. DTFT simbolica: senal completa
- 5. Volver

## 71. Entrada Fourier discreta
- 1. Lista o banco de datos
- 2. Expresion matematica x[n]
- 3. Volver

## 72. DTFT cancelada
- 1. Reintentar: mismos datos
- 2. Volver sin calcular

## 73. Unidades del espectro
- 1. w rad/muestra
- 2. Hz: indicar Ts en segundos
- 3. Volver

## 74. Analisis de fase
- 1. Fase desenrollada
- 2. Retardo de grupo (muestras)
- 3. Volver

## 75. Calculo cancelado
- 1. Reintentar: mismos datos
- 2. Volver sin calcular

## 76. Entrada serie discreta
- 1. Lista o banco: un periodo
- 2. Expresion x[n]: un periodo
- 3. Volver

## 77. Densidades espectrales
- 1. Energia: secuencia discreta
- 2. Energia: expresion continua
- 3. Periodograma con ventana (PSD)
- 4. Volver

## 78. Entrada de energia espectral
- 1. Lista o datos exportados
- 2. Expresion discreta
- 3. Volver

## 79. Metodo espectral
- 1. Periodograma anterior: |DFT|^2/N
- 2. PSD calibrada: un segmento
- 3. PSD Welch: promedio de segmentos
- 4. Volver

## 80. Continua en la PSD
- 1. Conservar media (incluye DC)
- 2. Restar media de cada segmento
- 3. Cancelar

## 81. Ventana espectral
- 1. Rectangular
- 2. Hann
- 3. Hamming
- 4. Blackman
- 5. Kaiser

## 82. Tipo de convolucion DFT
- 1. Lineal por DFT
- 2. Circular

## 83. Fourier: series y transformadas
- 1. Serie de Fourier continua
- 2. Serie de Fourier discreta
- 3. Transformada continua directa
- 4. Transformada continua inversa
- 5. Fourier discreta: DFT y DTFT
- 6. Densidad de energia y PSD
- 7. Convolucion y correlacion
- 8. Teoria y propiedades de Fourier
- 9. Volver al inicio

## 84. Operaciones de Fourier
- 1. Convolucion lineal o circular
- 2. Correlacion y autocorrelacion
- 3. Volver

## 85. Nyquist y aliasing
- 1. Criterio de banda y alias
- 2. Laboratorio visual de un tono
- 3. Volver

## 86. Graficos de aliasing
- 1. Tono original
- 2. Tono alias
- 3. Entrada al muestreador
- 4. Reconstruccion SINC
- 5. Error SINC - original
- 6. Espectros de lineas
- 7. Volver

## 87. Diagnostico de aliasing
- 1. Resumen del muestreo
- 2. Datos del tono
- 3. Filtro y senal muestreada
- 4. Interpretar el alias
- 5. SINC y error
- 6. Interpretar los espectros
- 7. Volver

## 88. Comparaciones del laboratorio
- 1. Original y alias
- 2. Original y SINC
- 3. Original y filtrada analogica
- 4. Muestras sin y con filtro
- 5. Filtrada analogica y SINC
- 6. Volver

## 89. Editar un parametro
- 1. Frecuencia f (Hz)
- 2. Amplitud A
- 3. Fase phi (rad)
- 4. Cantidad de muestras N
- 5. Periodo Ts (s)
- 6. Volver al resultado

## 90. Filtro antes de muestrear
- 1. Sin filtro
- 2. Cascada analogica RC
- 3. Volver

## 91. Cambio de tasa
- 1. Diezmar
- 2. Expandir con ceros
- 3. Interpolacion lineal
- 4. Interpolacion SINC
- 5. Retenedor orden cero

## 92. Entrada x[n]
- 1. Secuencia finita
- 2. Expresion matematica x[n]

## 93. SINC cancelada
- 1. Reintentar: misma entrada
- 2. Volver sin calcular

## 94. Metodo D/A
- 1. Retenedor de orden cero
- 2. Interpolacion lineal
- 3. Interpolacion SINC

## 95. SINC cancelada
- 1. Reintentar: misma entrada
- 2. Volver sin calcular

## 96. Niveles de cuantizacion
- 1. Sin offset: rango original
- 2. Con offset: nivel en 0

## 97. Metodo de cuantizacion
- 1. Redondeo
- 2. Truncamiento

## 98. Metodo de punto fijo
- 1. Redondeo
- 2. Truncamiento

## 99. Muestreo, conversion A/D y D/A
- 1. Muestrear: x(t) a x[n]
- 2. Analizar Nyquist y aliasing
- 3. Diezmar, expandir o interpolar
- 4. Reconstruir: x[n] a x(t)
- 5. Cuantizar y calcular SNR
- 6. Representar en punto fijo
- 7. Conceptos de conversion A/D y D/A
- 8. Volver al inicio

## 100. Coeficientes del filtro
- 1. Numerador b[k]
- 2. Denominador a[k]
- 3. Exportar b[k]
- 4. Exportar a[k]
- 5. Volver

## 101. FIR ideal
- 1. Pasa bajos
- 2. Pasa altos
- 3. Pasa banda
- 4. Rechaza banda

## 102. Ventana FIR
- 1. Rectangular
- 2. Hann
- 3. Hamming
- 4. Blackman
- 5. Kaiser

## 103. IIR biquad
- 1. Pasa bajos
- 2. Pasa altos
- 3. Pasa banda
- 4. Notch / rechaza

## 104. Diseno analogico RC
- 1. Pasa bajos RC
- 2. Pasa altos RC
- 3. Volver

## 105. Componente conocido
- 1. Fijar resistencia R
- 2. Fijar capacitor C
- 3. Volver

## 106. Filtros analogicos y digitales
- 1. Disenar FIR por ventanas
- 2. Disenar IIR biquad
- 3. Disenar filtro analogico RC
- 4. Filtrar una senal con b/a
- 5. Respuesta digital H(e^jw)
- 6. Polos/ceros: analizar o disenar
- 7. Transformacion bilineal H(s)-H(z)
- 8. Teoria y estructuras de filtros
- 9. Volver

## 107. Sistemas y control
- 1. Respuesta de segundo orden
- 2. Respuesta lineal H(jw)
- 3. Diagramas de Bode H(jw)
- 4. Respuesta discreta H(e^jw)
- 5. Realimentacion unitaria
- 6. Lugar de raices
- 7. Polos, ceros y estabilidad
- 8. Teoria de sistemas y control
- 9. Volver

## 108. Teoria por programa
- 1. Sistemas I: ejes 1-4
- 2. Sistemas I: Fourier
- 3. Sistemas I: muestreo/control
- 4. Sistemas II: procesamiento
- 5. Sistemas II: espectro
- 6. Sistemas II: filtros
- 7. Formulas clave
- 8. Instrucciones de uso
- 9. Volver

## 109. SignalLab 5.0
- 1. Novedades y limites
- 2. Ultima operacion registrada
- 3. Limpiar contexto temporal
- 4. Volver

## Entradas, salidas y convenciones

Ver las secciones 4–9 de `GUIA_SignalLab_5.0.md` en el proyecto HP de origen, además de la sección de convenciones en `MATRIZ_MIGRACION.md`. Entradas habituales: listas complejas, expresiones CAS, origen/índice, periodo/paso, cantidad, parámetros del modelo, ventana y destino; salidas: tablas complejas, fórmulas/condiciones, espectros, gráficos, exportaciones y recientes. Las rutas concretas varían por opción y conservan sus ayudas en el fuente HP.
