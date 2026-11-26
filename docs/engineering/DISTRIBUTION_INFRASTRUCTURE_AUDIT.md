# Auditoría de distribución y continuidad LTS

## Estado observado el 26 de noviembre de 2026

GitHub tiene `main` y `develop` como únicas ramas. `main` apunta a `acb9e387597bc076f269e4684963c58d516147c1` y declara 2.0.0 estable. La etiqueta anotada `v2.0.0` resuelve al commit `adfad5c093a236b0565f00f5e97845acf040ec96`. La API de Releases identifica `v2.0.0` como última estable y enumera su manifiesto firmado y sus instaladores de ambos sistemas. [Código del tag](https://github.com/Tincho1286/SignalLab-PC/tree/v2.0.0) · [Entrega LTS](https://github.com/Tincho1286/SignalLab-PC/releases/tag/v2.0.0)

El clon local conserva trece referencias históricas de trabajos anteriores, once `release/1.8.x` y dos `codex/*`. Los worktrees activos usan `main` y `develop`. Esas referencias locales preexistentes quedan inventariadas para una decisión de limpieza independiente.

## Compatibilidad y controles

| Hallazgo | Control implementado |
| --- | --- |
| El constructor y el publicador estaban dirigidos a `main`. | El constructor admite Preview desde `develop` y Stable/LTS desde el código LTS o su etiqueta. Comprueba el SHA íntegro y el canal declarado por la fuente. El publicador verifica pertenencia del SHA a `develop` para Preview y ascendencia de la última etiqueta LTS para mantenimiento desacoplado. |
| Un número usado por una preliminar no puede reutilizarse para LTS sin mover una etiqueta. | Las publicaciones nuevas reservan `2.0.x` a Stable/LTS y versiones a partir de `2.1.0` a Preview. Se conservan las etiquetas y entregas anteriores. |
| El actualizador 2.0.0 reconoce el manifiesto de esquema 1 mediante una lista exacta de campos. | Se conserva ese esquema. La firma incluye el canal y los hashes de los instaladores. La evidencia del Quality Gate y los comprobantes se adjuntan al expediente de la entrega. |
| El cliente histórico consulta `releases/latest` para la estable. | Preview conserva `prerelease=true` y `make_latest=false`. La entrega LTS conserva `prerelease=false` y solicita `make_latest=true` tras comprobar que avanza desde la última LTS. El cliente nuevo también valida la familia de versiones del feed estable. [API de GitHub Releases](https://docs.github.com/en/rest/releases/releases) |
| El publicador podía modificar una entrega existente. | El flujo nuevo valida localmente manifiesto, artefactos, hashes y procedencia. Conserva las releases activadas y permite terminar solamente un borrador compatible con exactamente los adjuntos verificados. |
| El salto aislado de 02C usaba un candidato firmado con el canal estable de ensayo. | En Fase 03, la firma temporal usa Preview. Se verifica el rechazo desde Stable/LTS, la entrega del archivo íntegro y la instalación nativa sobre la versión histórica en el entorno aislado. |

La preparación del candidato aprovecha los paquetes de la matriz del mismo SHA. Los artefactos de auditoría de Actions tienen retención temporal. El manifiesto público se firma después de la autorización correspondiente. [Política](RELEASE_POLICY.md) · [Quality Gate](phase_03/QUALITY_GATE_CRITERIA.md)
