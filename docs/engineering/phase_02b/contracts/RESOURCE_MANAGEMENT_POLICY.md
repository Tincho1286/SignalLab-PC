# Política de recursos

**Criterios previos.** Un presupuesto insuficiente rechaza antes de ejecutar. Dos trabajos que comparten una reserva tienen admisión determinista y liberan su reserva al salir. Cancelar, agotar plazo o fallar durante persistencia conserva la versión anterior. Los límites deben distinguir memoria temporal, resultados retenidos y serialización.

`ResourcePool` agrega contención voluntaria con admisión inmediata. El mismo pool debe compartirse entre los trabajos que se quieran coordinar. La operación reserva su estimación durante el cálculo. El flujo admite la suma conservadora de entrada, resultados retenidos y el mayor pico temporal. Reserva el conjunto una vez y pasa el plazo y el evento a cada etapa. Una cola o una cuota de proceso requeriría otro contrato.
