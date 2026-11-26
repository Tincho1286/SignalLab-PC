# SignalLab PC 2.1.0 Preview

Esta entrega incorpora el **Laboratorio de comunicaciones digitales**. Podés seguir un enlace desde los bits hasta las decisiones de recepción, o estudiar cada etapa por separado. Incluye PSK y QAM cuadrada con mapeo natural o Gray, pulsos rectangular, RC y RRC, y ruido AWGN calibrado por SNR, Es/N₀ o Eb/N₀.

El enlace compara la constelación transmitida con la recibida y muestra señal I/Q, diagramas de ojo, espectro y densidad espectral de potencia. El informe indica qué símbolos se usaron para calcular BER, SER y EVM, y separa las observaciones de las referencias exactas o aproximadas. La recepción puede usar un instante conocido, valores indicados por el usuario o una estimación con piloto. Cuando falta una alineación válida, el informe explica qué mediciones quedaron indeterminadas.

Workbench y la consola usan los mismos cálculos que la API Python. Un experimento guarda configuración, semillas, muestras, resultados y procedencia. Los barridos permiten cambiar el nivel de ruido, la modulación o los parámetros del pulso, comparar métricas y continuar una campaña a partir de las corridas guardadas. Las tablas se pueden exportar como CSV.

El candidato se prepara con portables e instaladores para Windows x64 y Linux x86_64. La opción Preview del actualizador es voluntaria. Stable/LTS mantiene su propia familia 2.0.x. [Ejemplos reproducibles](README.md) · [Política de las entregas](../RELEASE_POLICY.md)
