# Revisión funcional de 2.4.0 Preview

**Pendiente de la revisión del propietario.** [Descargas](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.4.0)

1. En **Redes multipuerto**, importá la muestra Touchstone de dos puertos. A 100 MHz, S₂₁ tiene parte real 0,8 y S₁₂ tiene parte real 0,02. Cambiá las referencias de 50 Ω a [50, 75] Ω, guardá el proyecto y comprobá los valores tras reabrirlo. [Muestra de prueba](evidence/candidate-1eb462e/asymmetry.s2p)
2. En **Líneas y adaptación**, usá un cuarto de onda para transformar 100 Ω a 50 Ω. La impedancia característica debe quedar cerca de 70,71 Ω. En la frecuencia de diseño, el marcador de Smith debe quedar cerca de Γ = 0. Consultá la pérdida fuera de ese punto.
3. En el diseñador analógico, elegí Bessel de segundo orden, Ωn = 4 rad/s y normalización de retardo. Verificá τg(0) = 0,25 s y enviá H(s) al análisis temporal.
4. En **Zoom FFT y Chirp-Z**, cargá una señal de prueba, superponé bins y compará su posición con el registro original. Guardá una ventana periódica y revisá la ganancia coherente y el ancho de ruido.
5. En **Enlace, ruido y dispositivos**, calculá el margen y estimá su incertidumbre. Reabrí la carpeta de campaña con los mismos parámetros y comprobá la continuidad.

Registrá el sistema operativo, configuración y resultado observado si aparece un defecto. La aceptación funcional y el merge se registrarán después de esa revisión.
