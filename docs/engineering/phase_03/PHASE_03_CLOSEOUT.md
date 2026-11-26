# Cierre técnico de Fase 03 · Digital Communications Lab

La fase parte de la consolidación de Engineering Core, verificada en Windows y Ubuntu sobre `a5eafa9a1e98116e84b57d3bb0e8881ea02b2931`. Pasaron 1 110 pruebas integrales, 150 casos preventivos por plataforma y 37 controles de calidad. Esa línea base conserva las decisiones de Fase 02C sobre MAT, recursos, pruebas de escritorio y distribución. [Línea base](PHASE_03_BASELINE.md)

## Arquitectura y herramientas

Las operaciones de comunicaciones se exponen como servicios Python independientes de Qt. Workbench y CLI llaman a las mismas funciones con contratos de bits, símbolos, reloj, constelación, señales I/Q, sincronización y resultados. La implementación reutiliza el Core para filtrado FIR, DFT, PSD, presupuestos, cancelación y almacenamiento. Una prueba de consola bloquea importaciones Qt y comprueba los mismos resultados de referencia. [Arquitectura](ARCHITECTURE.md) · [Contratos](SCIENTIFIC_CONTRACTS.md) · [Ejemplos](README.md)

El laboratorio admite bits manuales y sembrados, PSK y QAM cuadrada, etiquetado natural y Gray, pulsos rectangular, RC y RRC, AWGN calibrado, recuperación de símbolos y decisión dura. El enlace integrado genera BER, SER y EVM y ocho figuras. Las etapas se pueden ejecutar de forma independiente y reutilizar sus resultados. La sincronización de referencia conoce el retardo. La asistida recibe los parámetros de alineación y la estimada usa un piloto. Un perfil sin alineación válida conserva las señales y explica qué métricas quedaron indeterminadas.

## Evidencia independiente

Se verificaron geometría, Gray, energía y decisiones contra tablas y búsqueda exhaustiva, RC y RRC mediante cuadratura, y comportamiento gaussiano mediante distribuciones y regiones de decisión. El contraste con Komm se ejecutó fuera de la aplicación. El laboratorio mantiene separadas las tasas observadas, las referencias analíticas y las aproximaciones de vecinos para BER. Cinco perfiles Monte Carlo sin ISI y 32 transmisiones con RRC truncado contrastan condiciones estadísticas distintas. [Auditoría matemática](MATHEMATICAL_AUDIT.md) · [Catálogo de referencias](INTEGRATION_CATALOG.md)

## Datos, recursos y compatibilidad

El experimento registra semilla, subflujos, parámetros, reloj, muestras y huellas. Los proyectos JSON históricos siguen legibles. Los experimentos admiten SLPROJ y la API intercambia señales I/Q con SLBIN. El catálogo de barridos permite comparar y exportar métricas en CSV, preserva corridas confirmadas y se comprueba al recuperar. Las pruebas de cancelación verifican que la persistencia interrumpida conserve el estado anterior. [Trazabilidad](TRACEABILITY_MATRIX.md)

Los perfiles miden cómputo, escritura, lectura, memoria y latencia de cancelación. La admisión usa una estimación de memoria y las llamadas nativas cancelan cooperativamente. El inventario de dependencias nativas se conserva por plataforma. Las decisiones vigentes limitan MAT a archivos confiables y mantienen Authenticode como seguimiento E-04. Los manifiestos de actualización conservan su esquema firmado Ed25519. [Rendimiento](PERFORMANCE_REPORT.md) · [Seguridad](SECURITY_REVIEW.md) · [Riesgos](RESIDUAL_RISK_REGISTER.md)

## Distribución y continuidad

El candidato es 2.1.0 Preview. Stable/LTS mantiene 2.0.x desde `v2.0.0`. La política verifica que el SHA de Preview pertenezca a `develop`. El mantenimiento LTS parte de la última etiqueta estable mediante un checkout desacoplado y acredita su propia evidencia. Los hashes y comprobantes de los paquetes se vinculan al Quality Gate. El siguiente paso de distribución requiere autorización del propietario. La validación funcional de Preview precede a cualquier integración en `main`. [Política de ramas y entregas](../RELEASE_POLICY.md) · [Notas del candidato](PREVIEW_NOTES.md)

Para una futura Fase 04, conservar como caso de control el candidato AWGN de esta fase. Al agregar deterioros de canal, comprobar la identidad cuando se deshabilitan y el efecto sobre energía, reloj, alineación y reproducibilidad con oráculos que modelen cada deterioro. La autorización de esa fase es independiente. La Fase 10 figura en la hoja de ruta con sus propios criterios de consolidación y calificación. [Roadmap](../ROADMAP.md)

El dictamen y las cifras definitivas corresponden al SHA que identifica el [Quality Gate](QUALITY_GATE_REPORT.md).
