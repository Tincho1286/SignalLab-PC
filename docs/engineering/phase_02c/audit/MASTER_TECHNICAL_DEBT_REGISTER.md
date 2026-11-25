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

## Estado de continuidad autónoma

Referencias de arranque `7973a52` y `faef335`. Se cotejaron el historial de Fases 00, 01, 02A y 02B, la matriz 45673548563 y el estado limpio de develop. El registro anterior conserva la evaluación de origen.

| Hallazgo | Estado vigente | Criterio y verificación siguiente | Responsable |
| --- | --- | --- | --- |
| C-01 · E-01 | Bloqueado externamente para distribución | Rueda o binario corregido para los avisos aplicables, SBOM y portables por plataforma. | Empaquetado |
| C-02 · E-02 | Mitigación implementada y ya verificada en el candidato previo | Proceso MAT con cuota y plazos. Mantener alcance local y revisar aviso de h5py/HDF5 con las ruedas que lo resuelvan. | Importación |
| C-03, C-04 | Correcciones históricas resueltas en la referencia | Repetir la suite, oráculos y 150 casos preventivos sobre cada candidato posterior. Revisar cualquier fallo científico nuevo. | Core científico |
| C-05 · E-03 | Envolvente previa verificada. Admisión compartida ampliada | Ejecución simultánea de cálculo y guardado con rechazo previsible, liberación y reintento. Medir el nuevo candidato. | Ejecución |
| C-06a | SLPROJ robustecido, cobertura focal de 93,91 % de líneas y 86,00 % de ramas | Matriz completa, entradas inválidas, publicaciones y compatibilidad histórica. | Persistencia |
| C-06b | Hoja CAS v1 implementada y probada en Windows offscreen | JSON/SLPROJ, estado exacto, relaciones, restauración inerte, errores y recuperación sobre la matriz limpia. | CAS |
| C-06c | Recuperación asíncrona implementada y probada en Windows offscreen | Instancia exclusiva, bloqueo del disco sin bloquear la GUI, cancelación al cerrar, coalescencia y recuperación JSON histórica. | Escritorio |
| C-06d | Campaña de 48 corridas probada localmente con proyectos independientes | Repetir los hitos 1/4/8/16/32/48 en ambos runners limpios, preservar catálogo al interrumpir y verificar cada señal al abrir. | Rendimiento |
| C-07 · E-06a/b | Pendiente | 85 % de líneas y 75 % de ramas globales sin cambiar las reglas de medición. Repriorizar con el JSON de cobertura. | QA |
| C-08 · E-05 | Parcialmente resuelto | Flujo Windows real al 100 % documentado. Completar perfiles offscreen y reservar escritorio Linux real y multimonitor para actas disponibles. | Escritorio |
| C-09 · E-04 | Verificación técnica previa aprobada | Repetir salto desde 2.0.0 e inventario sobre el nuevo candidato. Firma y canal público conservan evaluación propia. | Distribución |
| C-10 y deuda D01–D10 | Seguimiento acotado a fallos comprobados | Preservar contratos Qt/Python/CLI y revisar diferencias introducidas en la persistencia y la admisión. Usar pruebas de producción y el grafo de dependencias. | Arquitectura |
| C-11 | Gate automático incorporado | Acreditar que faltantes, SHA cruzados y porcentajes insuficientes figuran como tales. Ejecutar sobre la matriz final. | QA |

Los nuevos resultados locales son exploratorios hasta que se validen en un mismo SHA limpio en Windows y Linux. [Evidencia histórica](../validation/evidence/ci-faef335.json)
