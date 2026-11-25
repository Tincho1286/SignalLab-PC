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
