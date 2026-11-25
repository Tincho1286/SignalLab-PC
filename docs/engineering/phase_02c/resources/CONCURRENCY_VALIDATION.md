# Concurrencia

`ResourcePool` tiene bloqueo de admisión y libera reservas con `finally`. Un pipeline reserva el conjunto estimado una vez y ejecuta los hijos dentro de esa reserva común. La suite comprueba contención, liberación por excepción, rechazo previo y cancelación en distintas etapas. `Project.stage_records` serializa escritores y publica el nuevo conjunto sólo después de verificar el estado final.

La GUI conserva su cola de trabajador. Una aplicación que use la API desde varios hilos puede compartir explícitamente un pool. La comprobación de residuos no equivale a observar la GUI y la API compitiendo en producción.
