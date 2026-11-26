# Criterios de salida de Fase 03

## Criterios científicos previos a la implementación

1. Las palabras de bits usan MSB primero y se reconstruyen exactamente, preservando la longitud útil y el relleno. Comparar Gray con la reflexión binaria y comprobar que los vecinos del ciclo PSK y de ambos ejes QAM difieren en un bit.
2. Los puntos y la energía de constelación se comparan con geometría independiente, con error absoluto de hasta 2 × 10⁻¹² para puntos y energía normalizados. En decisiones duras se verifica cada etiqueta y casos de observaciones internas y externas comparando contra la distancia directa a todos los puntos. La política de desempate se registra.
3. RC y RRC de pico teórico se contrastan con cuadratura del espectro ideal al menos en cero, singularidades, sus vecindades, límites de roll-off y muestras ordinarias, con error absoluto de hasta 2 × 10⁻¹¹. Verificar energía de coeficientes cuando se usa normalización unitaria, simetría, retardo de grupo, colas e ISI para los spans evaluados.
4. El canal reporta potencia y varianzas nominales según la derivación real y compleja. Para muestras gaussianas independientes se cotejan las varianzas medidas con los intervalos de χ². Verificar semillas, covarianza de cuadraturas y casos de magnitudes incompatibles.
5. El demostrador recupera los bits útiles sin ruido en los perfiles de referencia. El perfil de sincronización conocida compensa el retardo del filtro y declara sus orígenes. Los perfiles estimados demuestran recuperación ante desplazamiento entero y fase conocidos por el oráculo, y estado de indisponibilidad ante falta o ambigüedad del piloto. Guardar evidencia de la fase, la escala y la alineación.
6. BER y SER se verifican por conteo directo. EVM se verifica con vectores de referencia y errores deterministas, incluido EVM cero con estado de dB definido por el contrato. Monte Carlo informa tamaño y detención. Para el caso ideal independiente se contrasta la curva por intervalo binomial a nivel declarado, con control de comparaciones si se comprueban varios puntos. Para RRC truncado y mediciones correlacionadas se incorpora el error de truncamiento o un intervalo por réplicas independientes.
7. La configuración y un archivo de resultado de referencia recorren Workbench, Python y CLI. Deben conservar reloj, parámetros y huellas. Se comprueban en proyecto las figuras, unidades, referencia, procedencia, valores y retorno al resultado.
8. Un barrido permite recuperar solamente corridas completas después de interrupción y revalida huellas al continuar. Se comprueban cancelación, rechazo de entradas y archivos inválidos, presupuestos y compatibilidad histórica en Windows y Linux.

## Criterios de ingeniería

Cobertura global de líneas ≥85 % y ramas ≥75 %. Componentes críticos de Fase 03 y del Core con líneas ≥90 % y ramas críticas ≥85 % donde se especifican. Cero defectos P0 abiertos y cero P1 internos sin resolver. Matriz integral sobre un mismo SHA limpio en Windows y Linux, con empaquetados e instaladores verificados.

La evaluación exige rendimiento, memoria, latencia de cancelación y capacidad de respuesta documentados para perfiles pequeños, medianos y grandes. También exige revisión de seguridad, procedencia y atomicidad, compatibilidad, auditoría matemática independiente y trazabilidad. Los dictámenes de cierre, preparación para Fase 04 y distribución son separados. [Requisitos](PHASE_03_REQUIREMENTS.md)

La matriz integral recoge las pruebas `test_*.py` con el medidor de ramas del Core. Para cada nuevo módulo crítico se registra el resultado particular además del total de aplicación. Como referencia, la medición de 02C en `a80508c` superaba el mínimo entero de ramas por 33 en Windows y 30 en Linux. Los casos de rechazo, cancelación y recuperación de cada etapa deben ejercitarse durante su desarrollo, con evidencia focal antes de sumar el lote siguiente. [Cobertura de 02C](../phase_02c/testing/FINAL_COVERAGE_REPORT.md#cobertura-del-candidato-a80508c)
