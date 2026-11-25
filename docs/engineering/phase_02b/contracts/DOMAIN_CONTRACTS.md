# Contratos de dominio

Las solicitudes de aplicación nombran los campos con significado matemático. `Signal` conserva muestras, eje, dominio y metadatos de reloj. `Transfer` conserva coeficientes normalizados, período y ROC. `StateModel` sigue como modelo existente fuera de los servicios de esta fase. Cada adaptador convierte parámetros efectivos a procedencia tipada. Los errores de parámetros usan `ValueError`, los de recursos `ResourceLimitError`, el vencimiento `TimeoutError` y la cancelación `OperationCancelled`.
