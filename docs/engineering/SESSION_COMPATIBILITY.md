# Compatibilidad y procedencia de sesiones

| Formato | Versiones admitidas | Operación |
| --- | --- | --- |
| Proyecto JSON | 1 y 2 | Se puede abrir como biblioteca sin documentos de trabajo. Al fusionar se regeneran identificadores y se traducen sus referencias internas. |
| Sesión de escritorio JSON | 1, 2 y 3 | Se abren los resultados y el escritorio tras validar rutas, pestaña activa y referencias. Al volver a guardar se escribe la versión 3. |
| Señal individual JSON o CSV | Formatos de SignalLab | Se intercambian datos, unidades, índices y metadatos de señal, incluida la referencia de fase cuando existe. El grafo de resultados pertenece al archivo de proyecto. |

## Archivos históricos de prueba

| Archivo | Escritor de origen | Comprobaciones |
| --- | --- | --- |
| [Sesión v1](../../tests/fixtures/session-v1-draft-1.9.3.json) | 1.9.3 · `d917c2c2dfcf2e917ad8511756d349cd82d7ae9f` | Restaura la pestaña DFT, la señal compleja y el resultado hijo. Guarda como v3 y vuelve a cargar manteniendo identificadores, cronología y fase. |
| [Sesión v2](../../tests/fixtures/session-v2-draft-1.9.4.json) | 1.9.4 · `9cf00ce0b07349b648ff391b04134eda513940eb` | Misma verificación con la estructura del escritor v2. La inversa recupera las muestras en `n=-2,-1,0`, `Fs=4 Hz` y el tiempo inicial de −0,5 s. |
| [Sesión v3](../../tests/fixtures/session-v3-dft-2.0.0.json) | 2.0.0 · `adfad5c093a236b0565f00f5e97845acf040ec96` | Restaura la referencia histórica de DFT. Cambiar la opción sólo afecta cálculos nuevos. Los valores históricos se restauran sin recalcular. |

Cada archivo se generó desde el código del escritor indicado con una señal preparada para la auditoría, se calculó la DFT histórica y se guardó con su función `session.save`. Los esquemas v1 y v2 se exportaron con un borrador DFT activo que contiene la referencia al resultado de entrada. Las pruebas guardan otra copia en un directorio temporal.

La suite también ejercita errores de lectura y escritura, recuperación automática, referencias inexistentes, conclusiones simbólicas con condiciones y edición histórica de muestras. En una sesión v2, el resultado editado se conserva al migrar aunque la información de deshacer no exista en el formato original. Para esos registros se mantiene la invalidación de la fórmula. Los resultados DFT previos se identifican como referencia a `m=0`, con la excepción de los espectros angulares del estudio de ventanas, que ya aplicaban el índice `n`. [Convenciones](MATHEMATICAL_CONVENTIONS.md)

La muestra de sesiones históricas se limita a rutas, datos y controles concretos. Sigue pendiente ampliar con proyectos v1/v2 archivados externamente, ROC y sistemas con avances, diagramas y hojas CAS de cada época. La migración no garantiza que una versión anterior pueda interpretar la opción de fase agregada en el formato de controles.
