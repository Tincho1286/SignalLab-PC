# Frontend 0.13 — primera revisión del laboratorio

Se mantiene Segoe UI y la paleta oscura. La navegación de categorías usa listas compactas y las herramientas abiertas quedan accesibles por pestañas. Cada herramienta conserva sus propias entradas.

## Fórmulas

Las entradas de señales, muestreo, medidas y transformadas incorporan vista matemática y editor por tramos. Cada fila define un valor y una condición; se usa la primera condición verdadera. El último campo define el valor en los demás casos. Las expresiones where/Piecewise existentes se abren como filas. Los motores mantienen su representación interna restringida.

## Resultados

Los informes presentan fracciones, potencias, raíces, sumas e integrales compatibles con el renderizador local. Los tramos se presentan como casos. El texto original permanece disponible para exportación. Las expresiones que todavía no admiten composición matemática se conservan legibles como texto; no se ocultan condiciones ni resultados pendientes.

## Gráficos

Las secuencias discretas usan tallos y marcadores sin conexiones entre muestras en resultados, selector del proyecto, simulaciones de estados y coeficientes de Fourier. Los espectros continuos conservan curvas. La reducción visual de puntos conserva el comportamiento existente; no modifica los datos exportados.

Esta entrega es una revisión de interfaz en desarrollo, no una declaración de migración matemática completa. No se ejecutó la suite de pruebas para esta revisión.
