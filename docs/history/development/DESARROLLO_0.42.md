# SignalLab PC 0.42 — Lectura de transiciones

- Sombreado explícito de transiciones en FIR/IIR por especificaciones.
- Anchos izquierdo/derecho en rad/muestra, obtenidos de los límites del cálculo mostrado.
- Eje digital explícitamente lineal, con rango de 0 a pi.
- Nueva vista de módulo en amplitud, con tolerancias en las mismas unidades.
- Anchos numéricos también en el formulario y explicación en ayuda.

Revisión de código y sintaxis; sin pruebas funcionales. El caso de asimetría informado aún necesita los parámetros del caso para determinar su causa. No se alteraron los coeficientes ni se forzó simetría de la respuesta.
