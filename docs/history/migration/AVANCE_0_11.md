# Avance 0.11 — señales de proyecto, informes y gráficos

## Cambios de uso

- Selector de proyecto con búsqueda sin distinción de acentos, resultados recientes primero, cantidad de muestras, operación de origen y vista previa. Las entradas discretas y continuas filtran el dominio correspondiente. Los objetos de proyecto se conservan como instantáneas.
- Informes con párrafos y tablas de propiedades, etiquetas frecuentes en español y datos originales preservados para exportación. Todo el texto se escapa antes de presentarlo como HTML local; no se abren enlaces externos.
- En Muestreo, Fourier, filtros y transformadas, los controles desplazan de forma independiente. El gráfico y el informe tienen pestañas propias; los resultados ya no se apilan debajo de todo el formulario.
- Los cálculos básicos también separan el desplazamiento de controles del área de resultados. Los resultados comunes tienen pestañas Gráfico y Detalles.
- Botón Ampliar en los gráficos con barra de navegación: reutiliza el mismo lienzo y restaura su ubicación al cerrar. Conserva la figura y su estado de navegación.

## Evidencia

113 pruebas existentes aprobadas: work/regression-ui-results.txt. Revisión Qt offscreen de Muestreo, DTFT y respuesta en frecuencia a 1366×768 y 1100×700: work/ui-results-preview/verification.json. A tamaño mayor, los lienzos medidos tienen 373 px de alto en muestreo y 461 px en Fourier y filtros. Capturas de gráfico, informe y selector en la misma carpeta. Comprobación de ampliación/restauración con el lienzo y barra originales.

El autodiagnóstico del portable incluye ahora distribución de muestreo, búsqueda/selección de proyecto y conservación del texto del informe. Estas verificaciones cubren los recorridos indicados; no constituyen revisión visual de todas las opciones ni finalización de la migración HP.
