# Riesgos residuales de Fase 02C

| Identificador | Prioridad y condición | Mitigación y responsable | Criterio de revisión |
| --- | --- | --- | --- |
| C-01 · Qt, avisos y componentes embebidos | P1 de distribución, dependencia externa | Mantenimiento de empaquetado conserva controles de decodificación raster y seguimiento del runtime | Confirmar ruedas corregidas, reconstruir ambos portables y revisar sus rutas y componentes embebidos |
| C-02 · MATLAB y HDF5 | P1 si se incorporan archivos externos sin control | Mantenimiento del importador acota los archivos y la selección de datos locales. La ruta HDF5 usa un atributo nombrado y el lector clásico usa SciPy | Revisar actualización nativa, consumo y aislamiento antes de usarlo como ingreso masivo de archivos externos |
| C-05 · Consumo y plazo nativo | P1 para cargas fuera de la envolvente | Mantenimiento del Core aplica estimaciones, pool y puntos cooperativos | Verificar de nuevo con los tamaños previstos y excluir de esa envolvente la latencia garantizada de llamadas nativas |
| C-06 · Proyecto y CAS | P2, limitación operativa | Mantenimiento de persistencia conserva JSON y prueba resultados CAS publicados | Reevaluar formatos de proyecto para volúmenes superiores y definir persistencia de hojas CAS activas |
| C-07 · Cobertura | P2 con efecto en la puerta de cierre | Mantenimiento de pruebas controla regresiones con referencias y mide brechas por módulo | Cumplir los objetivos o aceptar cada excepción detallada |
| C-08 · Escritorio | P2 de validación | Mantenimiento de GUI aporta capturas y protocolo real | Adjuntar actas de Linux y DPI de sistema a 125 %, 150 % y 200 % según disponibilidad |
| C-09 · Actualización y firma | P1 limitado a distribución | Mantenimiento de releases conserva comprobaciones aisladas con firma descartable | Confirmar una versión superior, instalar desde 2.0.0 en un entorno aislado y comprobar autoría del artefacto Windows |
| C-10 · Rutas históricas Qt | P2, mejora futura | Mantenimiento del Core conserva la frontera del piloto y hereda las pruebas de paneles | Incorporar nuevas fronteras sólo con equivalencia demostrada |
