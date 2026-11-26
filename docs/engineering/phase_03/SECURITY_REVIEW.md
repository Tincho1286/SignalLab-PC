# Revisión de seguridad de Fase 03

El arranque aprovecha las dependencias ya inventariadas de 02C. Komm se usó en un directorio de auditoría para verificar referencias. El lock y el empaquetado del producto se heredan del Core. [Referencias y licencias](INTEGRATION_CATALOG.md) · [Inventarios 02C](../phase_02c/security/DEPENDENCY_CONTINUATION.md#verificación-de-e-01-en-64dc3c4)

La frontera de comunicaciones debe validar muestras finitas, dimensiones, tipos, reloj, energía y rangos de parámetros antes de asignar grandes buffers. Los órdenes de modulación y las configuraciones de barrido se comprueban con los presupuestos de cada etapa. Los registros de entrada tienen límites de tamaño y se validan antes de decodificar. La carga de proyectos utiliza la ruta histórica y se verifica antes de publicar o reemplazar resultados.

El catálogo de barridos debe resolver archivos previstos dentro de su directorio, comprobar huellas y descartar entradas corruptas. La escritura se prueba con interrupción y cancelación. En la entrega se verifican la inspección de los empaquetados, los avisos de dependencias y el alcance aprobado del lector MAT.
