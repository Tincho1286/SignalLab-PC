# Registro maestro de deuda técnica

| ID · origen | Hallazgo, causa y componente | Probabilidad · impacto · prioridad | Corrección, aceptación y prueba prevista | Estado y condición para Fase 03 |
| --- | --- | --- | --- | --- |
| C-01 · 01 | Qt y componentes nativos dependen de ruedas y paquetes. Los avisos y el alcance cambian según el binario. | Media · alto para una entrega · P1 | Consultar fuentes, identificar rutas, contrastar lock y SBOM de cada portable. | Abierto. Revisar exposición y parches aplicables. |
| C-02 · 00/01 | Algunos deserializadores de JSON leen por ruta. MATLAB HDF5 puede resolver dependencias en vez de leer exclusivamente la variable local. | Media · alto · P1 | Acotar lectura en el descriptor y limitar selección a datasets locales. Comprobar errores y entradas válidas. | Abierto. Bloquea si el laboratorio consume entradas sin controlar. |
| C-03 · 02B | El registro comprueba existencia de padres. DFT y flujo confían en valores mutables e IDs suministrados al guardar. | Alta · asociación científica incorrecta · P0 | Sellar contenido y parámetros, validar padres y resultados y comprobar reversión. | Abierto. Bloqueante. |
| C-04 · 02B | Las pruebas matemáticas dejan escenarios extremos y contratos entre motores por verificar. | Media · alto · P1 | Reejecutar oráculos de distintos dominios y cubrir fallos reproducidos. | Abierto. Bloquea mientras exista un defecto crítico conocido. |
| C-05 · 01/02B | Plazos cooperativos, pool voluntario y costos completos de serialización. | Alta con volúmenes grandes · alto · P1 | Medir memoria real y latencias y documentar envolvente. | Abierto. Limitar volumen del primer laboratorio. |
| C-06 · 01/02B | JSON de sesión copia arreglos. SLBIN cubre señales. La hoja CAS completa no forma parte de la sesión. | Alta con proyectos grandes · medio · P2 | Medir cargas previstas, especificar aislamiento de formatos y verificar compatibilidad. | Abierto. Revisar según tamaño y uso de CAS. |
| C-07 · 01/02B | Cobertura global y ramas críticas bajo objetivos. | Alta · medio · P2 | Medir brechas y agregar pruebas con resultados ni denominadores alterados. | Abierto. El cierre exige cumplir o aprobar excepciones. |
| C-08 · 01 | DPI real de Linux y multimonitor incompletos. | Media · medio · P2 | Matriz funcional y visual con alcance explícito. | Abierto para aceptación de escritorio. |
| C-09 · 01/02B | Los contratos descartables no acreditan actualización pública ni firma de Windows. | Media · alto para entrega · P1 | Separar pruebas locales, actualización entre versiones y condiciones de publicación. | Abierto para distribución. |
| C-10 · 00/02B | Acoplamiento Qt heredado, cancelación y despacho duplicados en rutas antiguas. | Media · medio · P2 | Revisión de dependencias y cambios sólo en fronteras con beneficio verificable. | Abierto. Medir antes de decidir expansión. |

Los SHA de resolución y el riesgo residual se registran a través de la [trazabilidad](../TRACEABILITY_MATRIX.md).
