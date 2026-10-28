# Versión 0.35

Implementado y empaquetado:
- IIR por especificaciones: Butterworth, Chebyshev I, Chebyshev II y elíptico digitales, con secciones de segundo orden.
- Selección de orden propia de cada familia y distinción entre orden del prototipo y filtro de banda.
- Explicación de cada familia en el formulario, informe y biblioteca; tolerancias lineales y frecuencias en rad/muestra.
- Se mantiene reutilización, exportación e informe de cumplimiento sobre la rejilla.
- Validación explícita de métodos, bordes y período finitos.

Base de implementación: scipy.signal.iirfilter, buttord, cheb1ord, cheb2ord y ellipord.
Referencia: https://docs.scipy.org/doc/scipy/reference/signal.html
Empaquetado completado correctamente y portable 0.35 copiado a la carpeta de entregas. Se conservan las versiones anteriores. No se ejecutaron pruebas funcionales.

- Límites de paso IIR coherentes en formulario, máscara e informe: 1−δp a 1. Excesos de hasta 1e-12 se señalan como límite numérico, sin certificar cumplimiento estricto.
