# Dimensionamiento de almacenamiento

Se dimensionó un escenario de evaluación, sin incorporar un motor de comunicaciones. El perfil de referencia procesa 65 536 símbolos a cuatro muestras por símbolo y conserva seis registros complejos de 262 144 muestras por ejecución. Un barrido de 16 configuraciones y tres semillas produce 48 ejecuciones y 288 registros.

| Magnitud | Por ejecución | Barrido completo |
| --- | ---: | ---: |
| Muestras complejas retenidas | 1 572 864 | 75 497 472 |
| Carga binaria a 16 B por muestra | 25,17 MB | 1,21 GB |
| JSON estimado a 92,7 B por muestra | 145,80 MB | 7,00 GB |

MB y GB son decimales y excluyen metadatos. Los 92,7 B salen del guardado histórico de dos señales con 262 144 muestras cada una. El tamaño textual depende de los valores. Las cifras de 48 ejecuciones estiman volumen. Los tiempos y picos observados corresponden al banco de menor escala que figura en la [envolvente operativa](../resources/OPERATIONAL_ENVELOPE.md).

## Contenedor de proyecto

`.slproj` admite proyectos o sesiones. El formato lleva una cabecera versionada, un manifiesto UTF-8 con un máximo de 16 MiB y 10 000 registros, muestras complejas de precisión doble en orden little-endian y SHA-256 sobre toda la secuencia anterior. Las muestras se escriben en bloques de 1 MiB. El cierre fuerza el vaciado del temporal y lo sustituye en el mismo directorio. Un guardado cancelado conserva el destino anterior. El digest verifica integridad y no acredita identidad del autor.

La reapertura comprueba la correspondencia entre cabecera, catálogo, longitud de datos y digest. La estimación de admisión es tres veces la carga binaria más ocho veces el manifiesto. Así, el barrido de ejemplo necesita 3,62 GB de presupuesto estimado antes de sumar el manifiesto. Con admisión del 35 %, implica más de 10,35 GB de RAM disponible al abrirlo como un solo proyecto. Un guardado de reemplazo necesita espacio para el archivo anterior y el temporal nuevo hasta confirmar el cambio.

El formato es opcional en Archivo → Sesiones → Guardar sesión completa. JSON y las sesiones históricas permanecen operables. La recuperación automática de escritorio todavía escribe JSON en el hilo de interfaz. El contenedor no convierte la operación en respaldos incrementales ni acredita la ejecución de un barrido de 48 corridas en un solo archivo. Antes de usar ese perfil, se deben medir proyectos con su catálogo efectivo, el pico de memoria al reabrirlos y el costo de recuperación automática.

## Alcance de CAS

Las sesiones conservan los resultados de CAS que se publicaron en Resultados. Hoja activa, variables y borradores pertenecen al escritorio actual. Quedan fuera de JSON y de `.slproj`. No se agregaron conversiones irreversibles ni reconstrucción de variables a partir de informes.

## Ejecución del escenario de referencia

`tools/measure_scientific_campaign.py --output work/distribution-audit/scientific-campaign.json` genera 48 proyectos independientes con seis registros cada uno. Construye y verifica un proyecto por vez. Cada corrida tiene una configuración y una semilla, enlaces entre los seis registros, eje, reloj y huella del archivo. Los hitos registran 1, 4, 8, 16, 32 y 48 corridas completas. Al cancelar durante la octava escritura se conserva el índice, se vuelven a verificar los siete proyectos previos y se reintenta la octava corrida. Los archivos temporales del banco se eliminan al terminar.

El primer ensayo Windows completó los 288 registros y 75 497 472 muestras, ocupó 1 208 085 276 B y midió 150,8 MiB de RSS pico. La medición end-to-end fue 22,7 s. La reapertura y validación de cada carga forma parte de ese tiempo. La verificación posterior de los primeros siete tras la interrupción amplía el ensayo del candidato de CI.

El autoguardado ahora escribe el contenedor binario en un escritor dedicado. Un ensayo Windows offscreen con dos registros de 262 144 muestras midió un mayor intervalo del temporizador de 29,27 ms con autoguardado y de 3 237,55 ms con escritura JSON síncrona. Se usa un temporizador de 10 ms. Para ese perfil, 100 ms permite detectar una pausa perceptible y es holgado frente al resultado local. En runners compartidos se registra la desviación con tres ensayos y se investiga junto con el perfil del host. [Integridad y contrato CAS](PERSISTENCE_INTEGRITY_REPORT.md)

En la matriz `54adaa0`, Windows ejecutó el escenario en 11,79 s con 170,0 MiB de RSS pico. Linux lo ejecutó en 12,18 s con 176,9 MiB. El conjunto completo ocupó 1 208 085 276 B en cada plataforma. Se revalidaron los siete proyectos previos después de cancelar la octava corrida y se comprobó la reapertura y procedencia de los 48. La capacidad verificada se aplica a proyectos independientes almacenados por lotes. [48 corridas Windows](../validation/evidence/windows-campaign-54adaa0.json) · [48 corridas Linux](../validation/evidence/linux-campaign-54adaa0.json) · [Contrato CAS v1](CAS_PERSISTENCE_VALIDATION.md)
