# SignalLab PC 0.82 · Compensación de módulo y fase en banda

27/10/2026. Compilación de desarrollo hacia 1.0. Se conservan versiones anteriores.

## Organización y uso

Ajustar ganancia y fase → Fase y compensación → Estudio. Se conservan la factorización de fase mínima/paso todo y su informe; el segundo estudio diseña un compensador FIR para el mismo H(z). Se mantienen las 31 familias y 72 rutas: no se crea otra herramienta para este caso.

El diseño pide banda en rad/muestra, cantidad de coeficientes, retardo entero objetivo, ganancia y regularización λ. Los parámetros aparecen sólo al elegir compensación. El resultado permite seleccionar C(z) o la transferencia H(z)C(z) cuando es representable con precisión. Las acciones comunes analizan, exportan o envían el sistema seleccionado.

## Método y alcance

Para un H(z) real y causal con polos numéricos estrictamente dentro del círculo unidad, se busca un FIR real causal C que aproxime ganancia·exp(−iωD) en la banda. Se minimiza el promedio de |H·C/ganancia−exp(−iωD)|² más λ·Σ|c[k]|². Se utiliza mínimos cuadrados con SVD, sin ecuaciones normales. La memoria se comprueba antes de formar la matriz y la cantidad de evaluaciones crece con longitud y retardo.

Una λ positiva penaliza coeficientes grandes a costa del ajuste. El informe no declara cumplimiento exacto: muestra RMS y máximo del error complejo relativo sobre una rejilla independiente más densa, condición/rango del problema y máximo muestreado de |C|. La acumulación de errores se escala para evitar desbordes innecesarios, verificada también con una ganancia de entrada de 1e308.

Los ceros no mínimos pueden compensarse aproximadamente permitiendo retardo. Un cero exacto en banda no puede producir ganancia no nula con C finito. No se cancelan raíces ni se estabilizan modos internos. La herramienta conoce H compleja: no deduce una fase única desde un módulo aislado. No garantiza la respuesta fuera de banda ni entre todos los puntos evaluados.

Se evalúa H·C por producto de respuestas. H conserva su representación, incluidas SOS. La transferencia conjunta se ofrece sólo cuando la forma resultante supera las comprobaciones de precisión; si pierde precisión, se conserva C y la comparación con una explicación, sin publicar ese equivalente. No se transforma forzosamente un FIR largo en raíces o secciones de menor precisión.

## Presentación y reutilización

- Informe matemático con C o G seleccionado, sus coeficientes cuando la fórmula es larga, el objetivo y la entrada H.
- Curvas de original, compensado y objetivo sobre ejes compartidos. El objetivo se dibuja sólo en la banda y con línea discontinua para distinguir coincidencias.
- Error de fase como ángulo principal respecto del objetivo, en radianes, con discontinuidades separadas y sin asignarlo en ceros. Retardo conjunto por suma de las derivadas analíticas de H y C.
- Comparación CSV con H, C, H·C y objetivo, conservando la banda y las unidades. Exportación/reutilización del sistema elegido mediante las acciones existentes.
- Las entradas editadas no alteran un resultado calculado ni su exportación hasta recalcular. La ayuda mantiene explicación conectada, referencia de campos e imagen de colores.
- Corrección de TransferResultReport: una fórmula de texto con símbolos tipográficos, como ·, pasa a texto legible si no admite representación matemática; ya no propaga un SyntaxError que interrumpa la carga de resultados.

## Evidencia dirigida

Cuatro casos en tests/test_phase_compensation.py: ganancia e inversa con retardo conocidas, simulación de impulso, aproximación de un cero exterior, cero en banda, efecto de λ, conservación de SOS y rechazos del alcance. Pasaron. Comprobación adicional de errores escalados con entrada 1e308: finita.

check_compensation_ui84.log: carga por fórmula, C/G y exportación seleccionada, ejes comunes y retardo analítico, CSV/JSON, envío a respuesta temporal, borrador marcado sin alterar la salida, pantallas 800×600 y 640×480, factorización anterior y ayuda ilustrada. Pasó. Se revisaron visualmente informe y comparación. El fallo tipográfico del informe se reprodujo y el recorrido completo pasó tras corregirlo.

No se ejecuta una campaña general de regresión ni de instalación. Siguen abiertos la reconstrucción módulo–fase general bajo hipótesis y los efectos de aritmética de implementación, además de la consolidación de la candidata 1.0 con alcance respaldado.
