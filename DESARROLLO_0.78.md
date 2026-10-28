# SignalLab PC 0.78 · Calculadora CAS

27/10/2026. Nueva hoja general de cálculo simbólico, inspirada en la forma de trabajo de xCAS y construida sobre SymPy, ya incluido en el portable. Conserva el escritorio oscuro, las siete áreas y los 31 problemas especializados; no agrega un menú público por cada operación CAS.

## Hoja de trabajo

Accesos: CAS en la barra superior, Calculadora CAS en el lateral, Herramientas y Ctrl+Shift+C. También aparece en la búsqueda. Es un documento reutilizable durante la sesión: cambiar de pestaña o cerrar/reabrir su documento no borra entradas ni variables.

Cada entrada tiene etiqueta [N] para recuperarla y salida rN para reutilizarla. ans conserva el último resultado válido. Enter evalúa; Shift+Enter permite una expresión multilineal dentro de paréntesis/corchetes; Ctrl+↑/↓ recupera comandos. Un error se presenta en la misma hoja sin aplicar el estado parcial. Cancelar detiene el proceso simbólico y conserva variables y ans.

Resultados con fórmulas matemáticas, conjuntos y matrices. En pantallas estrechas las matrices anchas muestran una vista parcial declarada; sus valores completos siguen disponibles para copiar y exportar. Hoja reúne variables/funciones, exportación HTML con imágenes incrustadas, texto completo, copia y nueva hoja. Los controles permanecen accesibles a 640×480.

## Operaciones disponibles

- Aritmética exacta, pi/e/i/j, complejos y potencias. Decimales de entrada interpretados como racionales exactos; approx(expr,dígitos) o N(expr,dígitos) para aproximar. Trigonometría en radianes. Multiplicación implícita básica como 2x y 3(x+1).
- Variables mediante a:=2 y funciones mediante f(x):=sin(a*x). Parámetros locales, consulta de variables y purge(a,f). Se evalúan los valores actuales al definir; los símbolos libres pueden resolverse con asignaciones posteriores al reutilizar una expresión.
- simplify, expand, factor, together, cancel, apart, trigonometría simbólica y sustitución simultánea.
- diff, integrate/int, limit, series, sum y prod; derivados de funciones simbólicas y operaciones pendientes se conservan como tales. La primitiva se presenta sin una constante arbitraria añadida.
- solve en complejos; solve_real para una incógnita real o desigualdad; sistemas mediante solve y linsolve. nsolve busca una raíz numérica local y lo indica expresamente.
- matrix/vector, operaciones matriciales, determinante, inversa, transpuesta, rango, traza, autovalores, núcleo y forma escalonada reducida. Índices desde cero.

La sintaxis soportada se documenta en F1, con un dibujo de entrada/resultado y secciones de uso. No se promete compatibilidad completa con Giac/xCAS ni un gestor general de supuestos. Los símbolos no se presuponen reales o positivos; conjuntos condicionales, integrales pendientes e infinitos no se convierten en respuestas finitas supuestas.

## Conexión con SignalLab

Resultado permite copiar una salida o su referencia, y cargar una expresión escalar en Crear una señal continua/discreta o en Analizar un sistema como H(s)/H(z). El cálculo se ejecuta después en el destino, con sus parámetros visibles. Se validan las variables y funciones que ese destino puede evaluar; no se convierten listas o matrices arbitrariamente en señales.

La hoja no exige una señal de proyecto y no llena Resultados con cada operación auxiliar. Se conserva durante esta sesión y puede exportarse a HTML/texto; no forma parte del guardado general de sesiones. Las herramientas de Laplace/Z y análisis mantienen sus recorridos propios.

## Implementación y evidencia dirigida

Entrada matemática mediante AST restringido, independiente del parser histórico que identifica x con t. El estado simbólico se reconstruye con constructores matemáticos autorizados, sin eval, pickle ni ejecución de texto Python. El cálculo usa el proceso aislado/cancelable existente. La salida de enteros grandes en ese proceso se condiciona a memoria de trabajo disponible, sin heredar el límite de dígitos de conversión de texto de Python. La tipografía/vista parcial limita sólo la representación, no el valor matemático.

Ocho casos dirigidos del motor: exactitud racional/decimal y multiplicación, independencia x/t, definiciones/referencias/purga, derivadas/integrales/límites/sumas y operaciones pendientes, ecuaciones/sistemas/conjuntos, matrices/índices/resultados anidados, sustitución/aproximación/fallos atómicos, raíz numérica, factorial exacto de 2000, notación científica exacta fuera del rango de float y aproximación recursiva conservando estructuras. Se verificó además rechazo de construcciones ajenas al lenguaje matemático y de dos expresiones independientes mezcladas en una celda.

Recorrido UI con el proceso CAS real: teclado → álgebra/cálculo/sistema/matriz → referencias y variables → exportación con fórmulas → envío a señal continua y H(s) → ayuda y búsqueda → cambio de documento → 800×600 y 640×480 con todos los grupos de acciones accesibles → matriz ancha sin desplazamiento horizontal → cancelación de una asignación en curso con el estado anterior intacto. Se revisaron capturas del escritorio CAS, hoja, ayuda y ventana compacta. No se realizó una campaña general de pruebas del resto de la app.

## Referencias

- [SymPy: parsing](https://docs.sympy.org/latest/modules/parsing.html). Se consultó como referencia; el texto de usuario no se entrega a parse_expr/eval.
- [SymPy: solvers](https://docs.sympy.org/latest/modules/solvers/solvers.html), para las operaciones de ecuaciones y soluciones numéricas locales.

Las versiones anteriores del portable se conservan. El trabajo hacia 1.0 continúa según CIERRE_1.0.md y la matriz de cobertura vigente.

Cierre del motor: 1e400, 1e-400 y complejos con esa notación permanecen exactos; se estima la memoria antes de construir exponentes grandes. approx mantiene listas/conjuntos/matrices y diccionarios; si el redondeo hiciera coincidir claves o soluciones diferentes se solicita más precisión. exact usa identificación simbólica y no promete recuperar un valor original desconocido tras redondearlo.
