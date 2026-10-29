# SignalLab PC 1.0.0 · primera versión estable

Fecha: 29 de octubre de 2026.

La primera estable consolida 29 herramientas agrupadas, 80 variantes y la calculadora CAS. Mantiene entradas independientes, biblioteca de resultados, gráficos externos y ayuda contextual ilustrada. Las formas de diseñar filtros comparten un documento; el análisis permanece en su lugar propio. Fourier separa transformada, dirección y cálculo.

## Corrección final

Se corrige el aviso falso Datos modificados después de diseñar RC o FIR. Los campos derivados que se actualizan al presentar una salida no se cuentan como entradas de la tarea activa. Los selectores internos que alimentan botones visibles siguen contando como entradas, aunque el selector original esté oculto.

El cálculo de un componente RC conserva la expresión del componente conocido. Sólo completa el componente faltante si la definición y ese campo siguen intactos; un resultado que llega después de editar no pisa esos cambios. El aviso de desactualización se mantiene para modificaciones reales hechas durante o después del cálculo.

## Identificación y documentación

La versión 1.0.0 se muestra en el título y en Ayuda → Acerca de SignalLab. El README explica cómo empezar, la cobertura vigente y la publicación. ALCANCE_1.0.md fija convenciones y límites; las notas anteriores se conservan como historia.

## Evidencia de cierre

Comprobaciones dirigidas del estado RC/FIR, selectores ocultos que sí son entradas, conservación de fórmulas y un resultado demorado después de editar. Cierre estructural de 29 problemas, 80 rutas únicas y sus enlaces de ayuda, con Señales Aleatorias conservada. Comprobaciones breves de DFT/inversa, coeficientes con pi y notación científica, y el ejemplo reportado de Z inversa reutilizado en CAS. Apertura, identificación de versión y Acerca de revisados.

Se utiliza el proceso portable ya confirmado por el usuario. No se repite una campaña de instalación ni una validación exhaustiva de todos los cálculos y resoluciones. Las evidencias específicas de métodos anteriores permanecen en las notas DESARROLLO y la matriz de cobertura.

La compilación se publica como estable en el repositorio privado, con ejecutable, documentación de alcance y SHA-256 verificados. Se conservan localmente la actual, la anterior y la primera.
