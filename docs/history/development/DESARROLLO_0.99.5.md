# SignalLab PC 0.99.5 · carga y reutilización coherentes

La entrega mejora el recorrido desde Resultados hacia las herramientas existentes. Se conserva el catálogo de 31 problemas y 80 variantes, sin añadir un menú por formato de dato.

## Cargar sistemas y expresiones

Cargar sistema → Usar un resultado anterior muestra sistemas tipados y expresiones guardadas en s/z. Se filtran por el dominio permitido y se excluyen sistemas tipados con avance cuando la operación requiere una realización causal. Una expresión se convierte al cargar mediante el lector común de funciones racionales; necesita coeficientes numéricos. El avance de una expresión se comprueba durante esa conversión. No se convierte automáticamente entre continuo y discreto.

La carga conserva la realización del sistema existente, secciones SOS y reloj físico. Para una expresión digital nueva se recupera un reloj único de su procedencia cuando existe; si es desconocido permanece desconocido. La conversión se publica como sistema con vínculo a la expresión original. Los editores de transferencia que reciben directamente la expresión la conservan visible y reutilizan los coeficientes convertidos sin redondearlos otra vez. Cargar prepara datos, no ejecuta el análisis.

Se aplica al cargador compartido de análisis, respuesta temporal, interconexiones, ajuste de ganancia/fase, precisión finita, estados y diseño por raíces. Un resultado X(s)/X(z) se interpreta algebraicamente como H; las condiciones y la ROC permanecen en su cálculo original y no se convierten en una hipótesis nueva de causalidad o estabilidad.

## Selector de resultados

El selector filtra expresiones por variable y unidad conocida. Las expresiones sin una unidad declarada toman la interpretación explícita de la herramienta de destino. Los sistemas se muestran mediante la fórmula de transferencia; los modelos de estados, mediante matrices. La búsqueda admite palabras en cualquier orden e ignora acentos. Los filtros usan metadatos sin copiar vectores completos.

La disposición cambia a lista y vista previa vertical en ventanas estrechas. En espacios pequeños se mantiene la información matemática y se oculta el gráfico de previsualización para conservar los controles de carga. Las figuras completas siguen disponibles en las herramientas. La vista previa de señales aplica la escala estable común.

## Expresiones temporales y medidas

Energía/potencia ofrece definiciones temporales de Resultados, incluidos resultados CAS y la señal de entrada de una medición anterior. No confunde el valor escalar de energía con una señal. Las expresiones por tramos se vinculan usando el texto que realmente guarda el editor, aunque cambie su escritura al cargarse.

Fourier algebraica filtra por variable y frecuencia angular; al cargar una secuencia completa para DTFT no impone el soporte unilateral 0…infinito. Se conserva su fórmula con escalones/tramos y se usa todo el eje, editable. Las condiciones originales se guardan con el pedido y se muestran en el informe. Si se edita la expresión, el siguiente cálculo no conserva un vínculo falso con la copia original. La copia entre variantes compatibles mantiene su procedencia.

Los informes de energía y potencia se presentan con secciones matemáticas para energía, potencia y RMS, estado exacto/condicional/pendiente, aproximación y alcance. La misma presentación se utiliza al consultar el resultado guardado: antes la vista genérica podía omitir las medidas y mostrar sólo el alcance. Fourier algebraica presenta también entrada, expresión y condiciones mediante el formato común.

## Evidencia puntual

Se recorrieron selector por dominio y unidad, exclusión de avances tipados, diálogo a 640×480, carga de una expresión como H(z) conservando reloj y padres, H(s) en respuesta temporal, fórmulas por tramos en medidas, copia entre variantes, informe de medidas en biblioteca e independencia tras editar. Las pruebas se limitaron a este recorrido; no se ejecutó una batería general ni una campaña del portable.

La versión sigue en desarrollo hacia 1.0. No añade ejecución de MATLAB arbitrario, guardado obligatorio de sesiones ni ampliaciones de Señales Aleatorias.
