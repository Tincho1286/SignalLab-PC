# Cobertura de Fase 02B

El denominador de la aplicación incluye las rutas vigentes de escritorio y módulos nuevos. La matriz mide líneas y ramas, junto con la ejecución de los procesos simbólicos. Los objetivos históricos siguen siendo 85 % global y 90 % de líneas en Muestreo y Fourier.

Para contratos nuevos se propone 85 % de líneas como referencia secundaria. El criterio principal es evidencia por ruta crítica en ambos sistemas. Incluye validación y resultado matemático, incompatibilidad, cancelación, plazo, admisión concurrente, integridad, fallo de reemplazo y reapertura. Las vías de interacción manual y los empaquetados se evalúan también fuera de coverage. No se excluyeron archivos nuevos ni se cambiaron tolerancias para una métrica.

| Ámbito | Windows · líneas / ramas | Ubuntu · líneas / ramas |
| --- | ---: | ---: |
| Aplicación | 77,96 % / 63,61 % | 77,94 % / 63,60 % |
| Muestreo | 92,11 % / 75,38 % | 92,11 % / 75,38 % |
| Fourier | 91,44 % / 60,71 % | 91,44 % / 60,71 % |
| Ejecución | 92,86 % / 77,27 % | 92,86 % / 77,27 % |
| Adaptadores DSP | 97,08 % / 83,33 % | 97,08 % / 83,33 % |
| Flujo DSP | 92,52 % / 58,33 % | 92,52 % / 58,33 % |
| Almacenamiento científico | 85,11 % / 67,86 % | 85,11 % / 67,86 % |
| Sesión de CLI | 85,94 % / 58,33 % | 85,94 % / 58,33 % |
| CLI de DSP | 98,68 % / 91,67 % | 98,68 % / 91,67 % |

El 85 % global sigue como objetivo orientativo, a 7,04 y 7,06 puntos respectivamente. Se mantiene la excepción documentada para el denominador de toda la aplicación y se conserva el seguimiento de rutas de escritorio. Los nuevos módulos medidos alcanzaron al menos 85 % de líneas y las pruebas ejercitan sus vías críticas. Las ramas del flujo y de sesión CLI muestran margen para probar otros errores y combinaciones de argumentos. [Evidencia de cobertura](phase02b-ci-8ad3066.json)
