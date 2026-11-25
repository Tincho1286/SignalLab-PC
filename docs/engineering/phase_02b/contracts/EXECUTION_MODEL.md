# Modelo de ejecución

`ExecutionContext` recibe un límite estimado de temporales en bytes, un plazo absoluto monotónico, un evento de cancelación y una función de progreso. El observador de `jobs` agrega comprobaciones a los puntos cooperativos existentes y se retira aunque la operación falle. El worker Qt conserva su propio evento. Una operación sin puntos internos verifica antes y después del bloque. La estimación del contexto se suma a las guardas propias del motor como condición de admisión.
