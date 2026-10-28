# Versión 0.33.1

Implementado y empaquetado en 0.33.1:
- Butterworth digital y por bilineal diseñado en secciones de segundo orden (SOS).
- Evaluación de frecuencia, tolerancias, polos y filtrado desde reposo en cascada.
- Conservación al reutilizar en respuesta temporal/frecuencia, normalizar ganancia, guardar sesión y exportar/importar JSON.
- Informe de secciones y explicación en biblioteca.
- Editar coeficientes vuelve a una definición polinómica. Los historiales no nulos y operaciones algebraicas siguen usando esa forma; no se promete precisión SOS en esos casos.

Empaquetado 0.33.1 completado correctamente y copiado a la carpeta de entregas. Se conservan los portables anteriores. No se ejecutaron pruebas funcionales.

- Revisión 0.33.1: la separación total/estado cero/entrada cero utiliza una única realización polinómica cuando hay historiales no nulos, evitando mezclarla con SOS. Con todos los historiales cero se conserva SOS.
