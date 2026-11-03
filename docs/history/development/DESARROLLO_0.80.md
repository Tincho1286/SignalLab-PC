# SignalLab PC 0.80 · Realización dentro del análisis

27/10/2026. Compilación de desarrollo hacia 1.0; se conservan las anteriores.

## Uso y organización

Analizar un sistema → Frecuencia y polos / ceros → Realización. Se reutiliza la definición numérica ya analizada; no se agrega una herramienta al catálogo ni se obliga a copiar los datos a otro formulario.

- El informe muestra la forma, los estados, las ecuaciones de cada sección y todos los coeficientes normalizados.
- Diagrama en ventana independiente: verde para integradores/retardos, ámbar para −a[k] y azul para b[k]. Los círculos suman; los sumadores de cada columna acumulan hacia arriba.
- El diagrama se abre ajustando el ancho disponible. Las cadenas largas conservan su escala vertical y se recorren con desplazamiento; no se aplastan para entrar completas en altura. Zoom, 100 %, ajustar ancho, arrastrar y Ctrl+rueda.
- Exportación completa SVG vectorial o PNG, independiente del zoom y de la parte visible de la ventana.
- Usar en espacio de estados envía A, B, C, D de la realización a análisis, simulación, frecuencia o transferencia. En discreto, T establece el reloj físico sin alterar H(z).
- Se conserva el último sistema calculado al editar el borrador; el aviso de datos modificados permanece. La nueva vista no recalcula H desde una entrada sin confirmar.
- Ayuda existente ampliada con un dibujo de colores y explicación de la cadena y del ingreso desde ecuaciones diferenciales/en diferencias.

## Cálculo y límites

Realización causal ordinaria de transferencias racionales propias continuas (integradores) y digitales sin avances (retardos). Forma directa II con realimentación −a[k] y salida b[k], sin eliminar raíces por proximidad ni asegurar minimalidad.

Si el Transfer conserva SOS, se construye una cascada de esas secciones: el diagrama, las ecuaciones y las matrices respetan su orden. Las matrices se ensamblan por conexión entrada/salida sin desarrollar un único polinomio. StateModel.from_transfer usa este mismo motor, por lo que la importación de filtros a estados también conserva esa estructura.

Se quitan sólo coeficientes extremos exactamente nulos que representan términos ausentes. No se recortan coeficientes pequeños. Una transferencia nula puede conservar modos internos del denominador; una cancelación externa no implica ausencia de estados. Las fórmulas que el análisis algebraico ya simplificó no permiten recuperar estados internos desconocidos.

Se contemplan ganancias estáticas sin estados, coeficientes complejos y FIR con retardos iniciales. Las matrices tienen costo cuadrático y se comprueba memoria antes de generarlas. El diagrama utiliza memoria lineal y desplazamiento; no hereda topes de muestras de la calculadora.

H(s) impropia se explica como necesidad de derivadores; H(z) con avance no se representa como una cadena causal de retardos. No se descartan esas partes ni se ofrece un diagrama distinto como si fuera equivalente. Los parámetros libres requieren valores numéricos, como las demás vistas numéricas del análisis.

## Evidencia dirigida

- tests/test_realization.py: cuatro casos que reúnen respuesta continua/complex, cancelaciones no eliminadas, FIR/retardos/IIR, SOS y simulación de impulso, estados importados, ganancias estáticas y casos fuera de alcance. Pasaron.
- tests/test_state_space.py: trece casos existentes afectados por la conversión compartida. Pasaron.
- check_realization_ui82.log: fórmulas continuas/discretas, ecuaciones y diagrama, SVG/PNG completos, envío a estados con T, resultado conservado tras editar, interfaz principal a 800×600 y 640×480, cadena de 30 retardos desplazable, cascada de tres secciones, impropias/avances explicados y ayuda ilustrada. Pasó.
- Revisión visual del diagrama continuo con todas sus entradas y salidas visibles al abrirse.

No se realizó una campaña general de instalación/regresión. Esta entrega cubre el pendiente de realización dentro de su alcance causal/propio; quedan abiertos los trabajos de módulo–fase/compensación y aritmética declarados en el cierre de 1.0.
