# Avance 0.12 — energía y potencia de expresiones

## Funciones y alcance

Se incorporan tres herramientas independientes en Señales: energía algebraica por intervalo, energía/potencia globales y energía/potencia periódicas. Cada una admite señales continuas x(t) y discretas x[n], complejas y con parámetros simbólicos.

En intervalos discretos ambos índices están incluidos; el promedio divide por N. En continuo el promedio divide por la duración. El análisis global integra o suma sobre todo el eje y calcula la potencia por límite simétrico: 1/(2R) en continuo y 1/(2M+1) en discreto. Si la energía total es finita demostrada, la potencia global es cero. En modo periódico se exige demostrar x(variable+periodo)=x(variable) antes de usar un periodo.

El resultado distingue finito, divergente, condicionado, no evaluado, no definido y no determinado. No se reemplaza una integral pendiente por cero. Se rechaza elevar Dirac u otras entradas no finitas al cuadrado como funciones ordinarias. Los parámetros libres se conservan y bloquean la creación de muestras hasta asignar valores en la expresión.

## Conexión entre herramientas

La definición y el resultado exacto se guardan como un cálculo de proyecto. Una ventana numérica opcional agrega otro cálculo con suma discreta o cuadratura trapezoidal de |x|², y una señal con padre enlazado a ese cálculo. Se conserva así la cadena definición → medida de ventana → muestras → Fourier u otra operación. La ventana no sustituye la definición infinita ni determina su clasificación global.

Los informes separan exacto y aproximación decimal. El resultado numérico utiliza las pestañas y gráficos ampliables de 0.11; no se apila un gráfico pequeño debajo del formulario. Editar la definición deshabilita el muestreo del cálculo anterior hasta recalcular.

## Evidencia

`test_expression_measures.py`: integrales y sumas complejas, extremos discretos inclusivos, energía bilateral exponencial, potencia de constante/escalón, periodicidad demostrada, parámetros, cero, potencia divergente, rechazo de distribuciones, ventanas numéricas, índices negativos y raíces complejas.

`test_toolbox.py`: definición → ventana → Fourier con procedencia, reutilización de definiciones y rechazo de usar la definición desactualizada desde el botón. Capturas offscreen en `work/measures-preview`. Registro completo: `work/regression-0.12.txt`. El diagnóstico portable incorpora solicitudes al proceso CAS y apertura del nuevo menú.

## Pendientes

No se garantiza resolución simbólica de cualquier expresión; las sumas, integrales y límites difíciles pueden quedar pendientes o requerir cancelación. La clasificación se emite sólo cuando las propiedades están demostradas. Falta la auditoría completa de todas las subopciones HP de medidas/densidad y señales con estados especiales. El objetivo general permanece abierto.
