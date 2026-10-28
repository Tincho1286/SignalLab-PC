# Avance 0.8 — Fourier algebraica conectada al cálculo numérico

## Cambios

- Transformada continua algebraica directa e inversa en frecuencia angular: X(w)=∫x(t)exp(-iwt)dt; inversa con 1/(2π). Se conservan condiciones y estado evaluado/no evaluado.
- DTFT algebraica de expresiones, con límites enteros finitos o infinitos. Las series geométricas sólo se resuelven cuando se demuestra la convergencia; las inciertas conservan condiciones y suma pendiente.
- Generación de registros numéricos desde expresiones resueltas sin condiciones pendientes. La fórmula, el registro y los resultados posteriores son objetos distintos unidos por procedencia.
- Unidades conservadas: continua rad/s, discreta rad/muestra, tiempo en segundos. Se evita reutilizar automáticamente una expresión con variable de salida incompatible.
- Evaluación restringida: no se convierten distribuciones, singularidades, parámetros sin asignar ni expresiones no evaluadas en muestras finitas. El parser puede rechazar funciones especiales aún no incorporadas; el resultado exacto se conserva.

## Evidencia

69 pruebas aprobadas (work/regression-0.8.txt). Nuevos casos: gaussiana y su inversa angular; exponencial bilateral; fase por desplazamiento; DTFT compleja finita; series geométricas derecha/izquierda y divergencia; rejillas complejas; rechazo de datos inválidos; recorrido Qt Fourier algebraica → muestras → inversa numérica y DTFT con unidades conservadas.

La inversa numérica del recorrido utiliza una ventana espectral finita: la prueba admite la tolerancia de truncamiento correspondiente. No se equipara esa aproximación con una inversa algebraica exacta.

Referencia de normalización del motor: documentación oficial SymPy, https://docs.sympy.org/latest/modules/integrals/integrals.html (consultada 22/10/2026). Se adapta la frecuencia ordinaria del motor a w/(2π) y se verifica contra pares conocidos.

## Pendientes del objetivo general

No se declara paridad total con HP ni equivalencia completa con MATLAB/Octave. Continúan pendientes los casos de distribuciones, señales con estados especiales, opciones HP no auditadas, integración homogénea de resultados, modelos de sistemas ampliados y revisión integral del portable/UI. Ver OBJETIVO_LABORATORIO_PC.md y MATRIZ_MIGRACION.md.
