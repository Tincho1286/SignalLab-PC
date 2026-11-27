# Seguridad y riesgos residuales de Fase 05

Las herramientas estadísticas conservan las dependencias fijadas de NumPy y SciPy. Los parámetros de consola, modelos y configuraciones se verifican antes de usarse como entradas de cálculo. La lectura de JSON comprueba archivos regulares, reserva memoria por tamaño y rechaza claves duplicadas. Los motores rechazan parámetros incompatibles y valores no finitos que no tengan una interpretación explícita en su contrato. [Seguridad de los importadores](../phase_02c/security/INPUT_SECURITY_VALIDATION.md)

Monte Carlo valida el destino de cada exportación antes de iniciar o continuar una campaña. Los bloques completos se publican con un escritor exclusivo. La huella de cada bloque incorpora la del anterior y el desplazamiento de sus réplicas. Al continuar, se comprueban la definición, el orden y los recuentos registrados. Los archivos anteriores permanecen disponibles hasta que se completa la sustitución. Las huellas detectan daños e inconsistencias, y la autenticidad de la descarga pública depende de la firma del manifiesto. [Rendimiento y recuperación](PERFORMANCE_REPORT.md) · [Política de entrega](../RELEASE_POLICY.md)

| Riesgo | Mitigación y evidencia exigida | Riesgo residual |
| --- | --- | --- |
| Entrada MATLAB externa | Se conserva la política de archivos confiables. El candidato vuelve a probar lectura clásica y HDF5, límites, reloj y cancelación. | Se mantienen las restricciones previas de importación. |
| Memoria y ejecución nativa | El presupuesto de trabajo se comparte entre operaciones y se verifica antes de ejecutar. Los perfiles de cancelación y recuperación se conservan por plataforma. | Las reservas son estimaciones. En un tramo nativo pueden transcurrir más muestras o tiempo hasta el próximo punto de cancelación. |
| Campañas en rutas compartidas | El ensayo nativo exige que un proceso contendor reciba un rechazo y pueda continuar cuando se libera el archivo. | Se califican sistemas de archivos locales de Windows y Linux. La semántica de bloqueo de unidades de red queda fuera del perfil acreditado. |
| Aceptación del escritorio | Se conservan pruebas funcionales automatizadas de navegación, cálculo, resultados y reutilización en dos plataformas. | La simulación Qt offscreen no acredita una sesión física ni un escalado DPI particular. |
| Dependencias y descargas | El paquete final debe acreditar el inventario nativo, el SBOM, el enlace OpenSSL, las licencias, la actualización aislada y la firma del manifiesto. | El seguimiento E-04 de distribución permanece independiente según la política aprobada. |

El expediente de la versión registrará los inventarios y recibos de los dos paquetes efectivamente construidos. [Evidencia de seguridad precedente](../phase_04/SECURITY_REVIEW.md) · [Criterios del Quality Gate](QUALITY_GATE_CRITERIA.md)
