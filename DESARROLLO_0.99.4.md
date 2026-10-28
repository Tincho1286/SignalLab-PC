# SignalLab PC 0.99.4 · Laplace bilateral y región de convergencia

Se amplía la herramienta existente de Laplace, sin añadir familias ni variantes al catálogo: siguen siendo 31 problemas y 80 variantes. Directa e Inversa conservan sus entradas y resultados; la interpretación se elige dentro del formulario.

## Directa bilateral

Se transforma la señal completa, incluidos sus valores para t<0. Los escalones, valores absolutos y tramos se separan en intervalos reales. Los intervalos acotados se integran sin imponer restricciones artificiales de colas; los intervalos infinitos aportan semiplanos cuya intersección define la ROC. Los bordes están excluidos. Los términos Dirac se integran por separado una sola vez, incluso en el origen.

La herramienta distingue una ROC vacía de un cálculo que el CAS deja sin evaluar. Una cancelación algebraica entre mitades divergentes no se ofrece como una transformada válida. Los tramos requieren que el motor pueda determinar su soporte real; las condiciones paramétricas se conservan.

## Inversa bilateral

Admite X(s) racional y un factor global exp(-d*s), con desplazamiento real finito. Se puede elegir la ROC a la derecha de todos los polos, a su izquierda, o mediante una línea vertical interior de parte real σ. σ admite constantes reales como pi y potencias decimales; no es un borde introducido por el usuario. Los polos determinan los bordes efectivos. Una línea que pasa por la parte real de un polo, o no puede separarse con precisión, se rechaza.

Cada fracción parcial conserva la multiplicidad del polo. Los términos derechos usan u(t); los izquierdos usan -u(-t) con la misma potencia temporal del par. Los términos polinómicos producen Dirac o sus derivadas. El desplazamiento global se aplica a todos los términos, sin cambiar la ROC. Parámetros simbólicos se admiten para elegir un semiplano; la línea interior requiere valores asignados.

Los polos algebraicos complicados se evalúan dentro de la fórmula, agrupando conjugados en senos y cosenos para entradas reales. Se conservan la descomposición exacta y un texto numérico de al menos 17 cifras; la vista redondeada no cambia el cálculo. Se evita expandir partes reales de RootOf sólo para ordenar bordes, que producía una demora innecesaria.

## Reutilización y ayuda

Copiar a la inversa traslada la interpretación y una ROC compatible cuando se pudo determinar. Si quedan condiciones paramétricas, el aviso pide revisarlas. La biblioteca de resultados conserva el pedido, la expresión y la ROC; al enviar una señal temporal a Laplace se usa bilateral para conservar ambos lados del tiempo. Las expresiones aproximadas de modos algebraicos se copian con sus números evaluados, sin exigir que el editor lea RootOf.

La ayuda contextual explica los controles con un dibujo de polos, franja verde, línea interior y soportes temporales con colores compartidos. La interpretación unilateral y la inversa causal siguen disponibles.

## Comprobación puntual

Se comprobaron pares directos/inversos derechos, izquierdos y mixtos, polo repetido, desplazamiento, impulso en cero y desplazado, derivada de impulso, señal sin ROC abierta, línea por un polo y modos cúbicos numéricos. Se recorrieron copia a la inversa, biblioteca en ambos sentidos, estado de datos modificados y render de informe/ayuda. No se ejecutó una batería general ni una campaña del portable.

La inversa bilateral no pretende cubrir cualquier X(s) trascendente, sumas de retardos diferentes ni distribuciones generalizadas sin ROC abierta. Es una entrega de desarrollo hacia 1.0; la meta estable permanece abierta.
