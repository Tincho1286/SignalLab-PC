# SignalLab PC 0.83 · Demora de Z inversa racional

27/10/2026. Corrección del caso enviado por el usuario. Se conservan los portables anteriores.

## Caso y causa

Entrada: (z^(-2)+z^(-3)-2*z^(-1))/(z^(-2)+1-z^(-3)). Al eliminar potencias negativas queda (-2*z^2+z+1)/(z^3+z-1).

La implementación anterior obtenía raíces con radicales y después intentaba cancelar y simplificar expresiones que las contenían. El diagnóstico acotado superó 12 segundos y se detuvo sólo ese proceso propio. Las cancelaciones simbólicas y la simplificación global podían crecer mucho para una fracción de tercer orden. Además, ordenar el texto de expresiones con coeficientes algebraicos provocaba evaluaciones numéricas innecesarias.

## Corrección

- Descomposición exacta mediante operaciones polinómicas de fracciones parciales; no se añade un polo artificial en cero al dividir X por z.
- Polos de orden uno y dos mediante expresiones exactas simples; factores racionales de mayor grado conservan raíces algebraicas definidas por su polinomio, sin expandir Cardano u otros radicales grandes.
- Aproximaciones ampliadas de los polos emparejadas con sus intervalos algebraicos exactos. La elección de radio usa intervalos de módulo para raíces algebraicas; radios que coinciden o no se separan con precisión se rechazan.
- Se mantienen términos derechos, izquierdos, polos repetidos e impulsos discretos de los términos polinómicos. Las expresiones con parámetros siguen siendo simbólicas.
- Para tramos causales iniciales con coeficientes racionales se generan muestras mediante recurrencia exacta. Otros intervalos usan evaluación modal de precisión ampliada y sólo al final pasan a doble precisión. El cambio de algoritmo no limita el intervalo permitido.
- El informe muestra una fórmula compacta con p[k] y A[k] cuando hace falta. Las tablas definen exactamente cada raíz y coeficiente; los decimales identifican las raíces y no reemplazan su definición.
- La fórmula exacta completa permanece en los datos del cálculo. Para imprimirla se evita reordenar términos de una manera que obligaba a evaluar de nuevo números algebraicos.
- Ayuda actualizada sin añadir menús ni cambiar la carga de datos.

## Resultado medido

El caso reportado tardó 0.153 s en una medición del motor. El recorrido de la interfaz, con un proceso simbólico nuevo, publicación, preparación del informe y 65 muestras desde n=−16, tardó 1.782 s. Son mediciones de esta máquina, no tiempos garantizados para cualquier entrada.

Con ROC exterior, las primeras muestras desde n=0 son 0,−2,1,3,−3,−2,6. Las regiones interior e intermedia producen otras secuencias y se comprobaron por separado.

## Comprobaciones dirigidas

Cuatro casos persistentes en tests/test_z_inverse.py: entrada reportada con tres ROC contrastadas contra integración de contorno por FFT; polos repetidos y términos finitos; parámetros/origen/radio sobre polo; grado cinco y coeficientes complejos. Pasaron tras el ajuste final de selección de ROC. El archivo de prueba reúne variantes del mismo fallo, sin ejecutar una campaña general del programa.

check_z_ui85.log: expresión exacta a través del proceso simbólico real, definiciones legibles, 65 muestras, ROC intermedia y ventana principal a 800×600 y 640×480. Pasó. Se revisó visualmente el informe.

Los pendientes generales de la 1.0 continúan en CIERRE_1.0.md. Esta entrega corrige la inversa racional y su presentación; no declara resuelta la reconstrucción módulo–fase ni la aritmética pendiente.
