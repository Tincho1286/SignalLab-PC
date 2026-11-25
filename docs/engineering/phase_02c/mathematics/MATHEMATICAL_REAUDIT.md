# Reauditoría matemática

Se revisaron las convenciones heredadas y la cobertura de oráculos por familia. La corrección de este paquete se concentra en el eje de PSD bilateral, donde calcular primero `1/Fs` podía desubicar todas las muestras aunque `Fs` y `Fs/N` fueran representables.

La regresión se verifica a través de `estimate_psd`, que delega en el mismo motor que usa la aplicación. El candidato necesita la suite integral de ambos sistemas antes de emitir el dictamen matemático.
