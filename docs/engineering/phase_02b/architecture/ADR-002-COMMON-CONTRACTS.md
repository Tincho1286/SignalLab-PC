# ADR 002 · Contratos comunes de aplicación

**Estado** aceptado para WP-02B.01. **Contexto.** DFT ya separa la solicitud, la ejecución, la salida y la publicación. Los motores cooperativos notifican progreso por `jobs`. Project almacena relaciones y session entrega archivos de forma atómica.

**Requisitos.** Usar el contexto sin importar Qt, conservar la firma DFT y el esquema de procedencia, y comprobar cancelación y plazo también en los puntos que ya tienen los motores.

**Alternativas.** Mantener contextos repetidos en cada adaptador simplifica el primer cambio y multiplica semánticas de cancelación. Un registro dinámico con solicitudes genéricas reduce el número de funciones y obliga a validar tipos durante la ejecución. Se eligen contexto y serialización de procedencia compartidos con solicitudes específicas por operación.

**Consecuencias y compatibilidad.** El trabajador Qt mantiene su contexto y puede coexistir con el observador local al hilo. `DFTExecution` se mantiene disponible como nombre compatible. `DFTResult` y los campos persistidos conservan su contrato. El progreso y el plazo requieren puntos cooperativos del backend. Las funciones nativas recuperan Python al terminar. Los diagnósticos son excepciones tipadas y los metadatos operacionales quedan fuera de la procedencia.

**Validación y revisión.** Las pruebas DFT existentes deben pasar y la observación anidada debe recuperar el contexto anterior, incluso ante una excepción. Revisar una interfaz polimórfica sólo si los adaptadores de DSP demuestran una necesidad común.
