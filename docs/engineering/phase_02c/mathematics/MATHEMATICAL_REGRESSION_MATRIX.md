# Matriz de regresión matemática

| Entrada | Propiedad comprobada | Evidencia |
| --- | --- | --- |
| Longitud 1, pares, impares y orígenes negativos | Eje, signos, orden, fase e IDFT | DFT piloto y contratos Fourier |
| Impulso, constante, tono y ruido con semilla | Parseval, bins y conservación de potencia | Auditoría preventiva y adaptadores DSP |
| Fs subnormal y amplitud 10⁻¹⁶⁰ | Origen −Fs/2 y potencia 4×10⁻¹¹ en Nyquist | `test_psd_small_finite_rate_preserves_centered_bins` |
| Paso no representable, NaN, infinito y parámetros incompatibles | Rechazo explícito antes de publicar | Contratos escalares, ejes y adaptadores DSP |
| Escala y cancelación extrema | Posiciones discretas, energía y normalización sin overflow intermedio evitable | `test_audit_numeric_clocks`, `test_math_sampling_fourier` |
| Polos, avances, ventanas y estados iniciales | Ganancia y fase, ROC, retardo y recurrencia | Contratos de sistemas y estado, transformadas y auditoría preventiva |
