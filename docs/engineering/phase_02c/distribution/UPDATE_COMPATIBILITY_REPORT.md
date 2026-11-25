# Compatibilidad de actualización

El ensayo entrega el instalador real con un manifiesto descartable y una clave Ed25519 de prueba. Comprueba la firma, el rechazo de esa clave por el verificador de producción, el tamaño, el hash y el instalador recibido. Las pruebas del actualizador incluyen destinos, comparación de versiones y operaciones fallidas en perfiles aislados.

El candidato y la estable pública declaran 2.0.0. El comparador debe rechazar un manifiesto de la misma versión como actualización. La transición desde la estable a una futura versión superior del candidato queda pendiente de una numeración y un artefacto autorizados en un canal aislado.
