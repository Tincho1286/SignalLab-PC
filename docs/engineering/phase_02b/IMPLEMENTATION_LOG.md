# Registro de implementación

## 25 de noviembre de 2026 · WP-02B.00

Partimos de `ff3e762` limpio. Se inspeccionaron `dft_application.py`, `jobs.py`, `resources.py`, `project.py`, `session.py`, los modelos y los accesos de Qt. Se contrastaron `git diff ce6846b ff3e762`, las referencias remotas, la matriz anterior, `pip check` y la familia DFT local. Se evaluó repetir toda la matriz antes de cambiar código. Se reutilizó la corrida exitosa del mismo árbol de código y se repitió la familia local. Se agregaron los cuatro documentos de partida y se actualizaron la hoja de ruta y el backlog. Seis pruebas locales pasaron y se comprobó el bloqueo de la actualización a Qt 6.12.1 por disponibilidad de ruedas. El estado verificable y los riesgos remanentes están en la [línea base](PHASE_02B_BASELINE.md). Este registro acompaña el commit `phase02b(wp00): establish verified baseline`. El siguiente paquete evalúa los contratos compartidos.
