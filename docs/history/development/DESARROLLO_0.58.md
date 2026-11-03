# SignalLab 0.58 · Exactitud del retardo de grupo

Corregida la vista Retardo de grupo de diseño/análisis de filtros. Antes derivaba la fase desenrollada sobre la rejilla del gráfico. Esto produce aliasing de fase si la variación entre puntos supera π; por ejemplo un retardo puro de 64 muestras sobre 17 puntos entre 0 y π podía parecer de retardo cero.

Ahora evalúa la derivada logarítmica de la transferencia directamente: Re(Σ k b[k]q^k/B − Σ k a[k]q^k/A), con q=exp(−jω), en digital. En analógico usa −Re(B′/B−A′/A), evaluada en s=jΩ. Los filtros SOS se evalúan por secciones. Las unidades son muestras o segundos según el dominio.

Los puntos singulares y las evaluaciones mal condicionadas se presentan sin dato; no se dibuja un retardo cero artificial. La derivada es analítica pero su evaluación sigue usando precisión numérica; cerca de ceros y polos hay límites de condicionamiento.

Comprobación acotada: retardo puro que antes se aliasaba, filtro de primer orden digital, primer orden analógico, coeficientes complejos, secciones SOS y puntos singulares. La ayuda describe el método nuevo. La curva de fase sigue siendo una representación muestreada y necesita una rejilla suficiente para mostrar variaciones rápidas.

Prioridad de la 1.0 actualizada: funcionalidad y exactitud. Guardado/recuperación de sesiones no es requisito por ahora. Modulación/demodulación excluidas; Señales Aleatorias postergada.

Referencia de definición y singularidades: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.group_delay.html
