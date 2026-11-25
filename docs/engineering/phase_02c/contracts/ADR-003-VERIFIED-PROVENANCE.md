# ADR-003 · Verificación por contenido en la publicación del Core

Se adopta SHA-256 de representaciones canónicas para las operaciones tipadas. Los identificadores de proyecto se conservan y se verifican contra el contenido utilizado. Así también se puede reutilizar un resultado con un registro equivalente después de reabrir o importar.

Los datos numéricos se procesan por bloques de hasta 16 384 elementos y los arrays contiguos se entregan al hash a través de un `memoryview`. Los registros serializados requieren una conversión acotada por bloque. Una transacción reutiliza las huellas ya verificadas entre sus etapas. Al reabrir se verifican únicamente los resultados con evidencia y sus padres. El formato histórico sigue siendo legible.

El costo de estas comprobaciones se mide junto con la publicación y la lectura para evaluar el componente de persistencia por separado del cálculo.
