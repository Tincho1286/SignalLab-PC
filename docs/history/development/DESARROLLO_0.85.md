# SignalLab PC 0.85 — expresiones de señales legibles

27/10/2026. Mejora común de presentación de resultados, sin nuevas rutas de navegación.

## Expresiones y propiedades

- Z inversa de z/(z−1/2), con ROC exterior: x[n]=(1/2)^n·u[n]. Con ROC interior: x[n]=−(1/2)^n·u[−n−1]. Se combinan los impulsos que completan o cancelan una muestra de borde.
- Identidad f[n]·δ[n−k]=f[k]·δ[n−k] cuando el valor está definido; extensión de soporte a través de un valor cero y agrupación de términos con el mismo escalón. Las operaciones son locales y acotadas: no se vuelve a simplificar globalmente una expresión con raíces algebraicas grandes.
- Presentación compartida en los informes matemáticos y el CAS: u[n], δ[n−k], escalones continuos, potencias, factoriales y coeficientes binomiales. Un borde distinto de la convención se indica con subíndice. En discreto, u[0]=1; en continuo, u(0)=1/2.
- Los tramos que conviene conservar se muestran como casos. Si forman parte de una suma o un producto, se utiliza una función auxiliar definida al lado de la expresión. Se conservan las condiciones y las prioridades de los tramos.
- La fórmula operativa exacta de Z, su ROC y su evaluación de muestras se conservan por separado de la presentación. El CAS mantiene los supuestos explícitos: no se presupone que cualquier símbolo libre sea entero.
- Las fórmulas anchas conservan el tamaño de letra y admiten desplazamiento horizontal, evitando volver a texto de programación por su ancho.

## Reutilización

Los campos numéricos evalúan productos con escalones o impulsos sólo en su soporte activo, evitando desbordes artificiales fuera de él. Se acepta Heaviside(v,valor) y KroneckerDelta(a,b). Las singularidades que se alcanzan dentro del soporte siguen siendo errores.

El CAS admite step y KroneckerDelta, vuelve a leer las expresiones simplificadas copiadas y restaura correctamente las parejas valor/condición de Piecewise. La biblioteca explica las convenciones y da un ejemplo de combinación de impulsos y escalones.

## Comprobación dirigida

Cuatro casos de prueba cubren equivalencia de muestras para secuencias derechas/izquierdas, polos repetidos y términos finitos, bordes y singularidades, evaluación numérica del soporte y el caso cúbico que antes demoraba. Los cuatro pasaron; el grupo tardó 0.82 s en el entorno local.

Se revisó el informe Qt de Z con las dos ROC, polos repetidos/algebraicos, tramos dentro de una expresión, símbolos compartidos y salida CAS en ventanas de 640/800 px. Se inspeccionaron las capturas de las fórmulas. Un cálculo CAS con n entero se copió y volvió a evaluar con el mismo resultado. La comprobación se limita a estos casos; la revisión general de uso continúa pendiente.

## Rumbo a 1.0

Sigue pendiente el trabajo ya registrado en CIERRE_1.0.md: reconstrucción general de módulo/fase y ejecución con productos, acumuladores y estados cuantizados, entre otros límites documentados. Esta entrega no declara finalizada la versión estable.
