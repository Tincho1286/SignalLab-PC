# Auditoría de recursos

El Core comprueba capacidad estimada y cancelación a través de `ExecutionContext` y `ResourcePool`. Los procesos simbólicos vigilan el plazo y limpian temporales y procesos al detenerse. Los controles de proyecto verifican pertenencia, contenido y cancelación dentro de una transacción en memoria.

La escritura JSON del CLI mantiene el control antes del reemplazo y consulta el estado cada 4096 fragmentos del codificador. El preflight y los checkpoints se mantuvieron separados del callback `before_commit`.
