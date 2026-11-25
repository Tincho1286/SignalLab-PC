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

## Proyectos, diagramas y CAS

| Archivo | Origen | Comprobaciones |
| --- | --- | --- |
| [Proyecto v1](../../tests/fixtures/project-v1-legacy-clock.json) | Reconstrucción del esquema legado a partir del escritor v2 | Recupera el período de muestreo heredado de 0,125 s y conserva la cadena de resultados al volver a guardar. |
| [Proyecto v2](../../tests/fixtures/project-v2-roc-cas-2.0.0.json) | Escritor de 2.0.0 | Preserva la ROC izquierda, el reloj y los resultados derivados. Verifica rechazo atómico con ROC o referencias inválidas, exportación transitiva y fusión con identificadores nuevos. |
| Diagramas [v1](../../tests/fixtures/diagram-v1-2.0.0.json), [v2](../../tests/fixtures/diagram-v2-2.0.0.json), [v3](../../tests/fixtures/diagram-v3-2.0.0.json) | Escritor de diagramas de 2.0.0 | Reapertura con ganancia continua, bloque discreto con reloj y realimentación negativa. Las funciones de transferencia se comparan con expresiones independientes. |
| Resultado CAS del proyecto v2 | Dos celdas ejecutadas en 2.0.0 | Importa el resultado publicado como `r1` en una hoja nueva y obtiene exactamente `12*x` al derivarlo. |

La muestra cubre los esquemas indicados y sus rutas de entrada. El v1 reconstruido verifica el lector y carece de un archivo de usuario contemporáneo como referencia. La persistencia de sesión conserva los resultados CAS publicados. La restauración de la hoja activa, las variables locales y los borradores del CAS sigue fuera de ese contrato. Las versiones anteriores pueden desconocer la opción de fase agregada al formato de controles. [Cierre de Fase 01](PHASE_01_CLOSEOUT.md)
