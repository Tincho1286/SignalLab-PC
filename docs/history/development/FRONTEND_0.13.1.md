# SignalLab PC 0.13.1 — reutilización entre herramientas

## Cambios
- Selector de las últimas 20 señales compatibles en cada entrada local. La búsqueda con vista previa sigue disponible para todo el proyecto.
- Acción «Enviar a…» en resultados de señales, con destinos según dominio. Para herramientas de dos entradas se elige cuál recibiría el resultado. Los parámetros se revisan antes de calcular en el destino.
- Se reutiliza el registro ya publicado; no se duplica una señal al enviarla. La cadena de procedencia se conserva al calcular en el destino.
- Las funciones por tramos sin valor por defecto mantienen ese estado, en lugar de completar con cero. El informe aclara cuándo no hay un valor definido fuera de sus casos.
- Corrección de la duración de los submenús «Enviar a…» en PySide6.

## Evidencia y alcance
Pasaron las 15 pruebas existentes de interacción de Toolbox, con ejecución autorizada fuera del entorno restringido. Una primera ejecución restringida se interrumpió tras fallos sin diagnóstico completo; no se cuenta como válida ni se atribuye su causa a la aplicación.

Además se abrieron las 60 rutas actuales; se reconstruyó el menú de envío tres veces, se activó DFT desde un resultado y se comprobó que conserva el identificador y origen sin duplicar el registro. Se comprobó la elección de otra señal reciente y la conservación de Piecewise sin rama por defecto. El informe de comprobación está en verificacion-frontend-0.13.1.json.

No acredita paridad con todas las funciones HP, equivalencia general con MATLAB/Octave, ni la finalización del rediseño. La transferencia rápida de sistemas y modelos de estados sigue pendiente; estos se reutilizan mediante sus selectores existentes. No se añadieron operaciones matemáticas en esta revisión.
