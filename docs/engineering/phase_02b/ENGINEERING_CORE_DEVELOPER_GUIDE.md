# Guía de desarrollo

El motor conserva su API científica. La capa de aplicación reúne parámetros efectivos, comprueba el contexto y prepara metadata. Qt sólo toma sus entradas y presenta la salida. La CLI conserva el mismo proyecto y la misma operación. Evitar dependencias desde motores y aplicación hacia los paneles.

La matriz verifica el mismo SHA en ambos sistemas. Cada prueba matemática debe indicar sus hipótesis y calcular el resultado con una fórmula independiente. Añadir una regresión cuando se corrige un defecto. Las pruebas de sesión usan archivos temporales con la API actual. [Pruebas y oráculos](operations/DSP_MATHEMATICAL_VALIDATION.md)
