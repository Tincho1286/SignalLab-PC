# SignalLab PC 0.99.8 · resultados al CAS y Z inversa por propiedades

## Reutilización en la hoja CAS

Las transformadas incorporan Enviar a CAS. Los menús de reutilización de señales, filtros, modelos de estado e informes numéricos ofrecen CAS; también se puede enviar una salida desde Resultados. No se agregan menús principales duplicados.

El envío agrega una celda a la hoja existente, sin vaciar variables, funciones ni supuestos. Conserva la expresión que se esté escribiendo. La nueva celda queda disponible como rN y registra su relación con la salida original. Las operaciones posteriores con esa referencia conservan la relación entre resultados.

Las expresiones mantienen su estructura matemática exacta cuando el motor la proporciona, incluidas raíces algebraicas de inversas Z y Laplace bilaterales. Se muestran las condiciones y ROC de origen. Operar con el resultado aplica las definiciones y supuestos de la hoja; la importación no redefine variables automáticamente.

Los sistemas se importan como H(s) o H(z), conservando avances y el período disponible. Las señales se importan como una matriz de eje y valores, y los modelos de estado como una tupla (A,B,C,D). Los informes numéricos aportan sus valores matemáticos; un texto sin datos calculables no se transforma artificialmente en una fórmula. Las cantidades numéricas conservan su precisión disponible.

## Z inversa mediante propiedades

Antes de la descomposición racional general se reconocen sumas de pares geométricos, polos repetidos y desplazamientos enteros. Se aplica linealidad y se agrupan las expresiones con el mismo soporte, conservando exponenciales y coeficientes exactos. Los términos que no corresponden a estos pares siguen el algoritmo general.

Para X(z)=2/(1-exp(-0.2)z^(-1))-1/(1-exp(-0.4)z^(-1)), con ROC |z|>exp(-1/5), se obtiene x[n]=(2 exp(-n/5)-exp(-2n/5))u[n]. No requiere añadir un impulso separado ni mostrar un cociente artificial de exponenciales. La ROC exterior, interior o elegida por radio determina el soporte de cada modo; no se presupone causalidad para todas las ramas.

## Evidencia y alcance

Comprobación dirigida del ejemplo exacto; muestras de pares repetidos, izquierdos, desplazados y con ROC mixta; importación de señal, transferencia, estado e informe numérico. Se recorrió el botón de envío desde la inversa Z, preservando variable y borrador existentes, y una simplificación posterior referida a la celda importada. Se comprobó el enlace de los resultados. No se ejecutó una batería general ni una campaña de pruebas del portable.

Se mantienen las 31 familias y 80 variantes del catálogo, además de la hoja CAS. Esta entrega continúa hacia 1.0; no declara resuelta toda la exactitud ni todo el alcance curricular. La ampliación de carga continua por pesos Dirac preparada aparte no forma parte de esta versión.
