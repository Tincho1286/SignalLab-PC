# Línea base de Fase 04

| Evidencia | Estado comprobado |
| --- | --- |
| Ramas oficiales al iniciar | `main` en `a94cd37d8fdc34fc16713a69af3e5bc30dd57600`. `develop` en `5a0bff926155f560fd6b071a010f422e587c8484`. |
| Distribución histórica | `v2.0.0` apunta a `adfad5c` y GitHub lo identifica como último release estable. `v2.1.1` apunta a `3ccb81a` y figura como prerelease. La etiqueta `v2.2.0` no existía al verificar el inicio de la fase. |
| Control de Fase 03 | Candidato 2.1.1 aprobado funcionalmente. La matriz integral del candidato y las comprobaciones de la integración en `main` terminaron en éxito. Se preservan la configuración QPSK Gray/RRC/AWGN y los casos de control sin ruido y con AWGN. [Candidato](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45861456445) · [Integración](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45873350407). |
| Multitrayecto previo | `5a0bff9` suma trayectorias enteras con coeficientes complejos, propaga el reloj y registra el origen. Su verificación inicial terminó en éxito. [CI](https://github.com/Tincho1286/SignalLab-PC/actions/runs/45875072214). |
| Brecha de partida | Faltaban el impulso coherente explícito, el PDP, sus momentos, la respuesta frecuencial, la normalización opcional y una medida de ISI. El canal era independiente del enlace integrado y de los barridos. |

El código de operación usa `Signal`, `ExecutionContext`, huellas de contenido y persistencia del Core. El enlace de Fase 03 separa bits, piloto y ruido en tres flujos reproducibles. El archivo de experimento valida configuración, roles, registros y huellas. Sus lectores históricos y convenciones quedan como pruebas de regresión. [Expediente de Fase 03](../phase_03/README.md) · [Política LTS](../RELEASE_POLICY.md).
