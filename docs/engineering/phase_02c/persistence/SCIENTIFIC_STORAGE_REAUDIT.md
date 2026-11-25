# Reauditoría de almacenamiento científico

SLBIN mantiene su estado experimental para intercambio de una señal. La comprobación de formato distingue metadatos, longitud y digest. El escritor usa un temporal en el mismo directorio, sincroniza el archivo y verifica la cancelación antes del reemplazo. El lector reserva antes de materializar muestras, controla cada bloque y rechaza duplicados en la cabecera.

JSON conserva su condición de formato predeterminado para proyecto y sesión. El diseño separa la decisión sobre un futuro contenedor de la corrección de integridad del formato existente.
