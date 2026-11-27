# SignalLab PC 2.2.0 Preview

El laboratorio de comunicaciones incorpora modelos de canal que podés usar por separado o combinar dentro de un enlace QPSK o QAM. Además del ruido, el enlace puede reproducir ecos, fading Rayleigh y Rician, dispersión Doppler, interferencia, pérdidas de propagación y errores de frecuencia, fase, reloj e I/Q. El informe conserva el orden de las etapas y el reloj de cada registro.

Las herramientas permiten comparar la respuesta impulsional, el perfil de potencia y retardo, la envolvente y la fase observadas frente a sus distribuciones teóricas, y el espectro Doppler. El enlace muestra BER, SER y EVM cuando hay una referencia de recepción válida e indica qué mediciones quedaron indisponibles cuando falta alineación.

Podés barrer parámetros de la transmisión y del canal en un mismo experimento. Cada corrida guarda la configuración, la semilla y las señales que intervienen, de modo que se puede reabrir o incorporar al proyecto. El catálogo permite retomar una campaña y exportar las comparaciones en CSV. Workbench, Python y la consola usan los mismos motores. [Ejemplos y condiciones de uso](README.md)

La edición está disponible para Windows x64 y Linux x86_64 como portable e instalador en el canal Preview. En una pantalla de 1366 × 768, el escalado de Qt al 200 % puede recortar la parte inferior de la ventana y de las figuras. Stable/LTS conserva la familia 2.0.x. [Descargas y notas publicadas](../../releases/v2.2.0.md) · [Política de distribución](../RELEASE_POLICY.md)
